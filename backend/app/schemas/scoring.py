from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InterviewScoreRead(BaseModel):
    """Full score record for an application."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    technical_foundation_score: Optional[float]
    project_depth_score: Optional[float]
    ml_understanding_score: Optional[float]
    coding_maturity_score: Optional[float]
    communication_score: Optional[float]
    motivation_score: Optional[float]
    completeness_score: Optional[float]
    authenticity_flag: Optional[bool]
    overall_score: Optional[float]
    rationale_json: Optional[Dict[str, Any]]
    scoring_version: Optional[str]
    created_at: datetime
    updated_at: datetime


class ScoreUpdate(BaseModel):
    """Partial score update (admin manual override or correction)."""

    technical_foundation_score: Optional[float] = Field(None, ge=0, le=10)
    project_depth_score: Optional[float] = Field(None, ge=0, le=10)
    ml_understanding_score: Optional[float] = Field(None, ge=0, le=10)
    coding_maturity_score: Optional[float] = Field(None, ge=0, le=10)
    communication_score: Optional[float] = Field(None, ge=0, le=10)
    motivation_score: Optional[float] = Field(None, ge=0, le=10)
    completeness_score: Optional[float] = Field(None, ge=0, le=10)
    authenticity_flag: Optional[bool] = None
