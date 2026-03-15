from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.application import ApplicationStatus


class AdminLogin(BaseModel):
    """Admin login request."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class AdminTokenResponse(BaseModel):
    """Successful login response containing JWT."""

    access_token: str
    token_type: str = "bearer"


class ReviewerNoteCreate(BaseModel):
    """Create a new reviewer note on an application."""

    note_text: str = Field(..., min_length=1, max_length=5000)


class ReviewerNoteRead(BaseModel):
    """Reviewer note for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    note_text: str
    admin_email: Optional[str] = None  # populated at route level
    created_at: datetime


class DashboardSummary(BaseModel):
    """Aggregated counts per status for the admin dashboard."""

    total: int
    received: int
    interview_in_progress: int
    completed: int
    shortlisted: int
    hold: int
    rejected: int
    needs_review: int

    model_config = ConfigDict(from_attributes=False)
