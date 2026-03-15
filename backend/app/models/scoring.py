from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.application import Application


class InterviewScore(Base):
    __tablename__ = "interview_scores"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    application_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Individual dimension scores (0–10)
    technical_foundation_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    project_depth_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ml_understanding_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    coding_maturity_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    communication_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    motivation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completeness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Derived / meta
    authenticity_flag: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    rationale_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    scoring_version: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default="1.0"
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="scores"
    )

    def __repr__(self) -> str:
        return (
            f"<InterviewScore id={self.id} app={self.application_id} "
            f"overall={self.overall_score}>"
        )
