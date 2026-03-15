from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreate(BaseModel):
    """Schema for creating a new student profile."""

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


class StudentRead(BaseModel):
    """Full student profile for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    phone: Optional[str]
    college: str
    degree: str
    branch: str
    year_of_study: int
    cgpa: Optional[float]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    created_at: datetime
