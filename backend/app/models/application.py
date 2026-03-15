from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.admin import AdminUser, ReviewerNote
    from app.models.document import Document
    from app.models.interview import InterviewSession
    from app.models.recommendation import Recommendation
    from app.models.resume_extraction import ResumeExtraction
    from app.models.scoring import InterviewScore
    from app.models.student import Student


class ApplicationStatus(str, enum.Enum):
    RECEIVED = "received"
    INTERVIEW_IN_PROGRESS = "interview_in_progress"
    COMPLETED = "completed"
    SHORTLISTED = "shortlisted"
    HOLD = "hold"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    student_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    internship_track: Mapped[str] = mapped_column(
        String(100), nullable=False, default="AI/ML"
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status"),
        nullable=False,
        default=ApplicationStatus.RECEIVED,
        index=True,
    )
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    statement_of_interest: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    application_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    submitted_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="applications")
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="application", cascade="all, delete-orphan"
    )
    resume_extraction: Mapped[Optional["ResumeExtraction"]] = relationship(
        "ResumeExtraction", back_populates="application", uselist=False
    )
    interview_session: Mapped[Optional["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="application", uselist=False
    )
    scores: Mapped[Optional["InterviewScore"]] = relationship(
        "InterviewScore", back_populates="application", uselist=False
    )
    recommendation: Mapped[Optional["Recommendation"]] = relationship(
        "Recommendation", back_populates="application", uselist=False
    )
    status_history: Mapped[List["ApplicationStatusHistory"]] = relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistory.changed_at",
    )
    reviewer_notes: Mapped[List["ReviewerNote"]] = relationship(
        "ReviewerNote",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ReviewerNote.created_at",
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id} status={self.status}>"


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    application_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
        index=True,
    )
    old_status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # admin email or "system"
    changed_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="status_history"
    )

    def __repr__(self) -> str:
        return (
            f"<ApplicationStatusHistory "
            f"app={self.application_id} {self.old_status}->{self.new_status}>"
        )
