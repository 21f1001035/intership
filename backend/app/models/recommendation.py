from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import Enum as SAEnum, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.application import Application


class RecommendationLabel(str, enum.Enum):
    SHORTLIST = "shortlist"
    HOLD = "hold"
    REJECT = "reject"
    NEEDS_REVIEW = "needs_review"


class Recommendation(Base):
    __tablename__ = "recommendations"

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
    label: Mapped[RecommendationLabel] = mapped_column(
        SAEnum(RecommendationLabel, name="recommendation_label"),
        nullable=False,
        index=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    narrative_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="recommendation"
    )

    def __repr__(self) -> str:
        return (
            f"<Recommendation id={self.id} label={self.label} "
            f"confidence={self.confidence}>"
        )
