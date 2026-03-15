from __future__ import annotations

import hashlib
import structlog
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_llm_provider
from app.core.config import settings
from app.core.security import generate_application_token
from app.llm.base import LLMProvider
from app.models.application import Application, ApplicationStatus, ApplicationStatusHistory
from app.models.document import Document
from app.models.student import Student
from app.schemas.application import ApplicationCreate, ApplicationRead
from app.services.audit_service import AuditService
from app.services.resume_parser import ResumeParserService
from app.services.storage import get_storage_service

router = APIRouter(tags=["applications"])
logger = structlog.get_logger(__name__)
_audit = AuditService()


def _get_application_by_token(
    application_id: UUID,
    application_token: str,
    db: Session,
) -> Application:
    """
    Retrieve an application and verify it belongs to the given token.
    Raises HTTP 404 / 403 on failure.
    """
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
    "/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new application",
)
def create_application(
    payload: ApplicationCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> Application:
    """
    Create a new student record (or reuse an existing one by email) and
    open a new application. Returns the application including the secret
    application_token the student will use to access subsequent endpoints.
    """
    # Upsert student by email
    student = db.query(Student).filter(Student.email == payload.email).first()
    if student is None:
        student = Student(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            college=payload.college,
            degree=payload.degree,
            branch=payload.branch,
            year_of_study=payload.year_of_study,
            cgpa=payload.cgpa,
            linkedin_url=payload.linkedin_url,
            github_url=payload.github_url,
        )
        db.add(student)
        db.flush()
    else:
        # Update mutable fields in case student reapplies with new info
        student.full_name = payload.full_name
        student.phone = payload.phone
        student.college = payload.college
        student.degree = payload.degree
        student.branch = payload.branch
        student.year_of_study = payload.year_of_study
        student.cgpa = payload.cgpa
        student.linkedin_url = payload.linkedin_url
        student.github_url = payload.github_url

    token = generate_application_token()
    application = Application(
        student_id=student.id,
        internship_track=payload.internship_track,
        status=ApplicationStatus.RECEIVED,
        source=payload.source,
        application_token=token,
    )
    db.add(application)
    db.flush()

    # Initial status history entry
    history = ApplicationStatusHistory(
        application_id=application.id,
        old_status=None,
        new_status=ApplicationStatus.RECEIVED.value,
        changed_by="system",
    )
    db.add(history)

    _audit.log(
        db=db,
        entity_type="application",
        entity_id=str(application.id),
        action="application_created",
        actor_type="student",
        actor_id=str(student.id),
        payload={"email": student.email, "track": application.internship_track},
        ip_address=request.client.host if request.client else None,
    )

    db.flush()
    logger.info(
        "Application created",
        application_id=str(application.id),
        student_email=student.email,
    )
    return application


@router.post(
    "/applications/{application_id}/resume",
    status_code=status.HTTP_200_OK,
    summary="Upload a resume PDF",
)
def upload_resume(
    application_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    application_token: str = Header(..., alias="X-Application-Token"),
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> dict:
    """
    Accept a PDF resume upload. The file is validated, stored, and parsed
    asynchronously. The structured profile is immediately extracted in-process
    for v1 (no task queue required for the basic flow).
    """
    application = _get_application_by_token(application_id, application_token, db)

    if application.status not in (
        ApplicationStatus.RECEIVED,
        ApplicationStatus.INTERVIEW_IN_PROGRESS,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upload resume for application in status '{application.status.value}'.",
        )

    # Validate file type
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted.",
        )

    file_bytes = file.file.read()

    # Validate file size
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )

    checksum = hashlib.sha256(file_bytes).hexdigest()

    # Save file
    storage = get_storage_service()
    storage_key = storage.save_file(
        file_bytes=file_bytes,
        filename=f"{application_id}_{file.filename}",
        subfolder="resumes",
    )

    # Persist document record
    doc = Document(
        application_id=application.id,
        document_type="resume",
        original_filename=file.filename or "resume.pdf",
        storage_key=storage_key,
        mime_type=file.content_type or "application/pdf",
        checksum=checksum,
        file_size_bytes=len(file_bytes),
    )
    db.add(doc)
    db.flush()

    # Parse resume synchronously (Celery task can be used instead in production)
    parser = ResumeParserService(llm_provider=llm_provider)
    extraction = parser.parse_resume(
        application_id=application.id,
        file_bytes=file_bytes,
        db=db,
    )

    _audit.log(
        db=db,
        entity_type="document",
        entity_id=str(doc.id),
        action="resume_uploaded",
        actor_type="student",
        actor_id=str(application.student_id),
        payload={"filename": file.filename, "storage_key": storage_key, "checksum": checksum},
        ip_address=request.client.host if request.client else None,
    )

    logger.info(
        "Resume uploaded and parsed",
        application_id=str(application_id),
        storage_key=storage_key,
    )
    return {
        "message": "Resume uploaded and processed successfully.",
        "document_id": str(doc.id),
        "storage_key": storage_key,
        "extraction_id": str(extraction.id),
    }


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationRead,
    summary="Get application status",
)
def get_application(
    application_id: UUID,
    application_token: str = Header(..., alias="X-Application-Token"),
    db: Session = Depends(get_db),
) -> Application:
    """
    Return the full application record. Requires the application token issued
    at creation time in the X-Application-Token header.
    """
    return _get_application_by_token(application_id, application_token, db)


@router.post(
    "/applications/{application_id}/complete",
    response_model=ApplicationRead,
    summary="Mark application as ready for interview",
)
def complete_application(
    application_id: UUID,
    request: Request,
    application_token: str = Header(..., alias="X-Application-Token"),
    db: Session = Depends(get_db),
) -> Application:
    """
    Called by the student after uploading their resume to confirm their submission
    is complete and they are ready to start the interview.
    """
    application = _get_application_by_token(application_id, application_token, db)

    if application.status != ApplicationStatus.RECEIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Application is already in status '{application.status.value}'. "
                "Only RECEIVED applications can be confirmed."
            ),
        )

    if application.resume_extraction is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload your resume before confirming submission.",
        )

    _audit.log(
        db=db,
        entity_type="application",
        entity_id=str(application.id),
        action="application_confirmed_by_student",
        actor_type="student",
        actor_id=str(application.student_id),
        ip_address=request.client.host if request.client else None,
    )

    logger.info(
        "Application confirmed by student",
        application_id=str(application_id),
    )
    return application
