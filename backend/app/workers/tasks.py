from __future__ import annotations

import structlog
from uuid import UUID

from celery import shared_task

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="app.workers.tasks.parse_resume_async",
)
def parse_resume_async(self, application_id: str, storage_key: str) -> dict:
    """
    Celery task: fetch the uploaded resume from storage, run PDF extraction
    and LLM normalisation, then persist the ResumeExtraction record.

    This is the async alternative to the in-process parsing used in v1.
    Enable it by calling `.delay()` from the route instead of calling
    ResumeParserService directly.
    """
    # Import here to avoid circular imports and to isolate DB/LLM setup
    from app.db.session import SessionLocal  # noqa: PLC0415
    from app.llm.openai_provider import OpenAIProvider  # noqa: PLC0415
    from app.services.resume_parser import ResumeParserService  # noqa: PLC0415
    from app.services.storage import get_storage_service  # noqa: PLC0415

    logger.info(
        "parse_resume_async started",
        application_id=application_id,
        storage_key=storage_key,
    )

    db = SessionLocal()
    try:
        storage = get_storage_service()
        try:
            file_bytes = storage.get_file(storage_key)
        except FileNotFoundError as exc:
            logger.error(
                "Resume file not found in storage",
                storage_key=storage_key,
                exc_info=exc,
            )
            raise self.retry(exc=exc) from exc

        llm_provider = OpenAIProvider()
        parser = ResumeParserService(llm_provider=llm_provider)
        extraction = parser.parse_resume(
            application_id=UUID(application_id),
            file_bytes=file_bytes,
            db=db,
        )
        db.commit()
        logger.info(
            "parse_resume_async completed",
            application_id=application_id,
            extraction_id=str(extraction.id),
        )
        return {
            "status": "success",
            "application_id": application_id,
            "extraction_id": str(extraction.id),
        }
    except Exception as exc:
        db.rollback()
        logger.error(
            "parse_resume_async failed",
            application_id=application_id,
            exc_info=exc,
        )
        raise self.retry(exc=exc) from exc
    finally:
        db.close()


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    name="app.workers.tasks.generate_final_recommendation_async",
)
def generate_final_recommendation_async(self, application_id: str) -> dict:
    """
    Celery task: generate the final LLM recommendation for a completed interview.
    Useful when the in-process recommendation generation times out.
    """
    from app.db.session import SessionLocal  # noqa: PLC0415
    from app.llm.openai_provider import OpenAIProvider  # noqa: PLC0415
    from app.models.application import Application  # noqa: PLC0415
    from app.models.interview import InterviewSession, InterviewStatus  # noqa: PLC0415
    from app.services.interview_orchestrator import InterviewOrchestrator  # noqa: PLC0415

    logger.info(
        "generate_final_recommendation_async started",
        application_id=application_id,
    )

    db = SessionLocal()
    try:
        llm_provider = OpenAIProvider()
        orchestrator = InterviewOrchestrator(db=db, llm_provider=llm_provider)

        application = db.query(Application).filter(
            Application.id == UUID(application_id)
        ).first()
        if application is None:
            raise ValueError(f"Application {application_id} not found.")

        session = application.interview_session
        if session is None:
            raise ValueError(f"No interview session for application {application_id}.")

        orchestrator._finalise_interview(session=session, application=application)
        db.commit()
        logger.info(
            "generate_final_recommendation_async completed",
            application_id=application_id,
        )
        return {"status": "success", "application_id": application_id}
    except Exception as exc:
        db.rollback()
        logger.error(
            "generate_final_recommendation_async failed",
            application_id=application_id,
            exc_info=exc,
        )
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
