from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.interview import InterviewStatus, InterviewTheme, SenderType


class InterviewStartResponse(BaseModel):
    """Returned when a new interview session is created."""

    session_id: UUID
    first_message: str
    theme: InterviewTheme
    turn_count: int


class InterviewMessageCreate(BaseModel):
    """Student message payload."""

    message_text: str = Field(..., min_length=1, max_length=10000)


class InterviewMessageRead(BaseModel):
    """Single message in a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sender_type: SenderType
    message_text: str
    theme: Optional[str]
    turn_number: int
    created_at: datetime


class InterviewStateResponse(BaseModel):
    """Full state of an ongoing or completed interview."""

    session_id: UUID
    status: InterviewStatus
    current_theme: InterviewTheme
    turn_count: int
    messages: List[InterviewMessageRead]
    is_complete: bool

    model_config = ConfigDict(from_attributes=False)


class BotReplyResponse(BaseModel):
    """Response after submitting a student message."""

    session_id: UUID
    bot_message: InterviewMessageRead
    current_theme: InterviewTheme
    turn_count: int
    is_complete: bool
