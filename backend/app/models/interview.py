from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.application import Application


class InterviewTheme(str, enum.Enum):
    MOTIVATION = "motivation"
    PROJECT_DEEP_DIVE = "project_deep_dive"
    ML_FUNDAMENTALS = "ml_fundamentals"
    CODING_DEPTH = "coding_depth"
    AVAILABILITY = "availability"
    COMPLETE = "complete"


class InterviewStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SenderType(str, enum.Enum):
    STUDENT = "student"
    BOT = "bot"
    SYSTEM = "system"


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

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
    session_status: Mapped[InterviewStatus] = mapped_column(
        SAEnum(InterviewStatus, name="interview_status", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=InterviewStatus.NOT_STARTED,
        index=True,
    )
    current_theme: Mapped[InterviewTheme] = mapped_column(
        SAEnum(InterviewTheme, name="interview_theme", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=InterviewTheme.MOTIVATION,
    )
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # JSON dict mapping theme name -> number of follow-ups used so far
    followup_counts: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="interview_session"
    )
    messages: Mapped[List["InterviewMessage"]] = relationship(
        "InterviewMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewMessage.turn_number",
    )

    def __repr__(self) -> str:
        return (
            f"<InterviewSession id={self.id} status={self.session_status} "
            f"theme={self.current_theme} turns={self.turn_count}>"
        )


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id"),
        nullable=False,
        index=True,
    )
    sender_type: Mapped[SenderType] = mapped_column(
        SAEnum(SenderType, name="sender_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    message_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )  # structured metadata from LLM
    theme: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="messages"
    )

    def __repr__(self) -> str:
        return (
            f"<InterviewMessage id={self.id} sender={self.sender_type} "
            f"turn={self.turn_number}>"
        )
