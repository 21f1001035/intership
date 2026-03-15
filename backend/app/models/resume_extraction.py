from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.application import Application


class ResumeExtraction(Base):
    __tablename__ = "resume_extractions"

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
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    extraction_provider: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g. "openai"
    extraction_model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g. "gpt-4o"
    extraction_version: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # semantic version of our prompt
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="resume_extraction"
    )

    def __repr__(self) -> str:
        return f"<ResumeExtraction id={self.id} app={self.application_id}>"
