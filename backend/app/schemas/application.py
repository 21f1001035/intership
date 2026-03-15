from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.application import ApplicationStatus
from app.schemas.student import StudentRead


class ApplicationCreate(BaseModel):
    """Everything needed to submit a new application (student info + interest)."""

    # Student fields
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    college: str = Field(..., min_length=2, max_length=255)
    degree: str = Field(..., min_length=2, max_length=100)
    branch: str = Field(..., min_length=2, max_length=100)
    year_of_study: int = Field(..., ge=1, le=6)
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)

    # Application fields
    internship_track: str = Field(default="AI/ML", max_length=100)
    source: Optional[str] = Field(None, max_length=100)


class ApplicationRead(BaseModel):
    """Full application read schema including nested student data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    internship_track: str
    status: ApplicationStatus
    source: Optional[str]
    application_token: str
    submitted_at: datetime
    completed_at: Optional[datetime]
    student: StudentRead


class ApplicationStatusUpdate(BaseModel):
    """Payload for admin to update the status of an application."""

    status: ApplicationStatus
    reason: Optional[str] = Field(None, max_length=1000)


class ApplicationListItem(BaseModel):
    """Compact application summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    internship_track: str
    status: ApplicationStatus
    submitted_at: datetime
    completed_at: Optional[datetime]

    # Denormalized student fields for list display
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    student_college: Optional[str] = None
    student_branch: Optional[str] = None
    overall_score: Optional[float] = None
    recommendation_label: Optional[str] = None
