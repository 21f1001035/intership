from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.security import create_access_token, verify_password
from app.models.admin import AdminUser, ReviewerNote
from app.models.application import Application, ApplicationStatus, ApplicationStatusHistory
from app.models.interview import InterviewMessage
from app.models.recommendation import Recommendation
from app.models.scoring import InterviewScore
from app.models.student import Student
from app.schemas.admin import (
    AdminLogin,
    AdminTokenResponse,
    DashboardSummary,
    ReviewerNoteCreate,
    ReviewerNoteRead,
)
from app.schemas.application import ApplicationListItem, ApplicationRead, ApplicationStatusUpdate
from app.schemas.interview import InterviewMessageRead
from app.schemas.scoring import InterviewScoreRead
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)
_audit = AuditService()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=AdminTokenResponse,
    summary="Admin login — returns JWT",
)
def admin_login(
    credentials: AdminLogin,
    db: Session = Depends(get_db),
) -> AdminTokenResponse:
    """Authenticate an admin user and return a signed JWT access token."""
    admin = db.query(AdminUser).filter(AdminUser.email == credentials.email).first()
    if admin is None or not verify_password(credentials.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive.",
        )

    # Record last login
    admin.last_login = datetime.now(timezone.utc)

    token = create_access_token(data={"sub": admin.email})
    return AdminTokenResponse(access_token=token, token_type="bearer")


# ---------------------------------------------------------------------------
# Applications — list and detail
# ---------------------------------------------------------------------------

@router.get(
    "/applications",
    response_model=List[ApplicationListItem],
    summary="List applications with optional filters",
)
def list_applications(
    status_filter: Optional[ApplicationStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None, description="Search by student name or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[ApplicationListItem]:
    """
    Return a paginated list of applications.
    Optional filters: status, search (name/email).
    """
    query = (
        db.query(Application)
        .join(Application.student)
        .outerjoin(Application.scores)
        .outerjoin(Application.recommendation)
    )

    if status_filter:
        query = query.filter(Application.status == status_filter)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            (func.lower(Student.full_name).like(search_term))
            | (func.lower(Student.email).like(search_term))
        )

    total = query.count()
    applications = (
        query.order_by(Application.submitted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for app in applications:
        item = ApplicationListItem(
            id=app.id,
            internship_track=app.internship_track,
            status=app.status,
            submitted_at=app.submitted_at,
            completed_at=app.completed_at,
            student_name=app.student.full_name if app.student else None,
            student_email=app.student.email if app.student else None,
            student_college=app.student.college if app.student else None,
            student_branch=app.student.branch if app.student else None,
            overall_score=app.scores.overall_score if app.scores else None,
            recommendation_label=app.recommendation.label.value if app.recommendation else None,
        )
        result.append(item)
    return result


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationRead,
    summary="Get full application detail",
)
def get_application_detail(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> Application:
    """Return the full application record including student info."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    return application


@router.get(
    "/applications/{application_id}/transcript",
    response_model=List[InterviewMessageRead],
    summary="Get interview transcript",
)
def get_transcript(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[InterviewMessageRead]:
    """Return all interview messages for the given application in order."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    if application.interview_session is None:
        return []

    messages = (
        db.query(InterviewMessage)
        .filter(InterviewMessage.session_id == application.interview_session.id)
        .order_by(InterviewMessage.turn_number)
        .all()
    )
    return [
        InterviewMessageRead(
            id=m.id,
            sender_type=m.sender_type,
            message_text=m.message_text,
            theme=m.theme,
            turn_number=m.turn_number,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.get(
    "/applications/{application_id}/scores",
    summary="Get scores and recommendation for an application",
)
def get_scores(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> dict:
    """Return scores and recommendation label/rationale for the given application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    scores = (
        db.query(InterviewScore)
        .filter(InterviewScore.application_id == application_id)
        .first()
    )
    recommendation = (
        db.query(Recommendation)
        .filter(Recommendation.application_id == application_id)
        .first()
    )

    scores_data = None
    if scores:
        scores_data = {
            "technical_foundation_score": scores.technical_foundation_score,
            "project_depth_score": scores.project_depth_score,
            "ml_understanding_score": scores.ml_understanding_score,
            "coding_maturity_score": scores.coding_maturity_score,
            "communication_score": scores.communication_score,
            "motivation_score": scores.motivation_score,
            "completeness_score": scores.completeness_score,
            "overall_score": scores.overall_score,
            "authenticity_flag": scores.authenticity_flag,
        }

    rec_data = None
    if recommendation:
        rec_data = {
            "label": recommendation.label.value if recommendation.label else None,
            "confidence": recommendation.confidence,
            "rationale": recommendation.rationale,
            "narrative_summary": recommendation.narrative_summary,
        }

    return {"scores": scores_data, "recommendation": rec_data}


# ---------------------------------------------------------------------------
# Status management
# ---------------------------------------------------------------------------

@router.post(
    "/applications/{application_id}/status",
    response_model=ApplicationRead,
    summary="Update application status",
)
def update_application_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> Application:
    """Admin override to change the status of an application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    old_status = application.status.value
    application.status = payload.status

    # Record in history
    history = ApplicationStatusHistory(
        application_id=application.id,
        old_status=old_status,
        new_status=payload.status.value,
        changed_by=current_admin.email,
    )
    db.add(history)

    _audit.log(
        db=db,
        entity_type="application",
        entity_id=str(application.id),
        action="status_changed",
        actor_type="admin",
        actor_id=str(current_admin.id),
        payload={
            "old_status": old_status,
            "new_status": payload.status.value,
            "reason": payload.reason,
        },
        ip_address=request.client.host if request.client else None,
    )

    logger.info(
        "Application status updated by admin",
        application_id=str(application_id),
        old=old_status,
        new=payload.status.value,
        admin=current_admin.email,
    )
    return application


# ---------------------------------------------------------------------------
# Reviewer notes
# ---------------------------------------------------------------------------

@router.post(
    "/applications/{application_id}/notes",
    response_model=ReviewerNoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a reviewer note",
)
def add_reviewer_note(
    application_id: UUID,
    payload: ReviewerNoteCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> ReviewerNoteRead:
    """Append a reviewer note to the application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    note = ReviewerNote(
        application_id=application_id,
        admin_user_id=current_admin.id,
        note_text=payload.note_text,
    )
    db.add(note)
    db.flush()

    return ReviewerNoteRead(
        id=note.id,
        note_text=note.note_text,
        admin_email=current_admin.email,
        created_at=note.created_at,
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get(
    "/dashboard/summary",
    response_model=DashboardSummary,
    summary="Dashboard summary counts by status",
)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> DashboardSummary:
    """Return counts of applications grouped by status for the admin dashboard."""
    rows = (
        db.query(Application.status, func.count(Application.id))
        .group_by(Application.status)
        .all()
    )
    counts: dict = {row[0].value: row[1] for row in rows}
    total = sum(counts.values())

    return DashboardSummary(
        total=total,
        received=counts.get(ApplicationStatus.RECEIVED.value, 0),
        interview_in_progress=counts.get(ApplicationStatus.INTERVIEW_IN_PROGRESS.value, 0),
        completed=counts.get(ApplicationStatus.COMPLETED.value, 0),
        shortlisted=counts.get(ApplicationStatus.SHORTLISTED.value, 0),
        hold=counts.get(ApplicationStatus.HOLD.value, 0),
        rejected=counts.get(ApplicationStatus.REJECTED.value, 0),
        needs_review=counts.get(ApplicationStatus.NEEDS_REVIEW.value, 0),
    )
