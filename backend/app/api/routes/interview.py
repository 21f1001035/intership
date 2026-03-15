from __future__ import annotations

import structlog
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_llm_provider
from app.llm.base import LLMProvider
from app.models.application import Application
from app.models.interview import InterviewStatus, SenderType
from app.schemas.interview import (
    BotReplyResponse,
    InterviewMessageCreate,
    InterviewMessageRead,
    InterviewStartResponse,
    InterviewStateResponse,
)
from app.services.audit_service import AuditService
from app.services.interview_orchestrator import InterviewOrchestrator

router = APIRouter(tags=["interview"])
logger = structlog.get_logger(__name__)
_audit = AuditService()


def _verify_application_token(
    application_id: UUID,
    application_token: str,
    db: Session,
) -> Application:
    """Return the Application or raise 404/403."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    if application.application_token != application_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid application token.",
        )
    return application


@router.post(
    "/interview/{application_id}/start",
    response_model=InterviewStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an interview session",
)
def start_interview(
    application_id: UUID,
    request: Request,
    application_token: str = Header(..., alias="X-Application-Token"),
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> InterviewStartResponse:
    """
    Create a new interview session for the given application and return the
    first question. Requires the X-Application-Token header.
    """
    _verify_application_token(application_id, application_token, db)

    orchestrator = InterviewOrchestrator(db=db, llm_provider=llm_provider)
    try:
        session, first_msg = orchestrator.start_interview(application_id=application_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return InterviewStartResponse(
        session_id=session.id,
        first_message=first_msg.message_text,
        theme=session.current_theme,
        turn_count=session.turn_count,
    )


@router.get(
    "/interview/{application_id}",
    response_model=InterviewStateResponse,
    summary="Get current interview state",
)
def get_interview_state(
    application_id: UUID,
    application_token: str = Header(..., alias="X-Application-Token"),
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> InterviewStateResponse:
    """
    Return the full interview state (session status, theme, all messages) for
    the given application. Useful for reconnecting / resuming.
    """
    _verify_application_token(application_id, application_token, db)

    orchestrator = InterviewOrchestrator(db=db, llm_provider=llm_provider)
    state = orchestrator.get_interview_state(application_id=application_id)

    session = state["session"]
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No interview session found for this application. Please start one first.",
        )

    messages_read = [
        InterviewMessageRead(
            id=m.id,
            sender_type=m.sender_type,
            message_text=m.message_text,
            theme=m.theme,
            turn_number=m.turn_number,
            created_at=m.created_at,
        )
        for m in state["messages"]
    ]

    return InterviewStateResponse(
        session_id=session.id,
        status=session.session_status,
        current_theme=session.current_theme,
        turn_count=session.turn_count,
        messages=messages_read,
        is_complete=state["is_complete"],
    )


@router.post(
    "/interview/{session_id}/message",
    response_model=BotReplyResponse,
    summary="Submit a student message and get bot reply",
)
def send_message(
    session_id: UUID,
    payload: InterviewMessageCreate,
    request: Request,
    application_token: str = Header(..., alias="X-Application-Token"),
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> BotReplyResponse:
    """
    Submit the student's reply to the current interview question.
    The orchestrator evaluates it, updates scores, and returns the next bot message.
    """
    from app.models.interview import InterviewSession  # noqa: PLC0415

    # Load session and verify the token against its application
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found.",
        )

    _verify_application_token(session.application_id, application_token, db)

    orchestrator = InterviewOrchestrator(db=db, llm_provider=llm_provider)
    try:
        updated_session, bot_msg = orchestrator.process_student_message(
            session_id=session_id,
            message_text=payload.message_text,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    bot_msg_read = InterviewMessageRead(
        id=bot_msg.id,
        sender_type=bot_msg.sender_type,
        message_text=bot_msg.message_text,
        theme=bot_msg.theme,
        turn_number=bot_msg.turn_number,
        created_at=bot_msg.created_at,
    )

    is_complete = updated_session.session_status == InterviewStatus.COMPLETED

    return BotReplyResponse(
        session_id=updated_session.id,
        bot_message=bot_msg_read,
        current_theme=updated_session.current_theme,
        turn_count=updated_session.turn_count,
        is_complete=is_complete,
    )
