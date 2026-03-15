from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Resume Parsing
# ---------------------------------------------------------------------------

class EducationEntry(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    year_start: Optional[str] = None
    year_end: Optional[str] = None
    cgpa: Optional[str] = None


class ProjectEntry(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    role: Optional[str] = None
    impact: Optional[str] = None
    duration: Optional[str] = None


class InternshipEntry(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class ResearchEntry(BaseModel):
    title: Optional[str] = None
    institution: Optional[str] = None
    description: Optional[str] = None
    publication: Optional[str] = None


class ResumeStructuredProfile(BaseModel):
    education: List[EducationEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    internships: List[InternshipEntry] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    research_experience: List[ResearchEntry] = Field(default_factory=list)
    publications: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    inferred_strengths: List[str] = Field(
        default_factory=list,
        description="Up to 5 strengths inferred from the overall profile",
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Important fields that are absent from the resume",
    )


# ---------------------------------------------------------------------------
# Answer Evaluation
# ---------------------------------------------------------------------------

class AnswerEvaluation(BaseModel):
    theme: str
    quality: str = Field(
        ..., description="One of: strong | adequate | vague | off_topic"
    )
    score: float = Field(..., ge=0, le=10)
    reasoning: str
    follow_up_needed: bool
    follow_up_question: Optional[str] = None
    move_to_next_theme: bool


# ---------------------------------------------------------------------------
# Next Question
# ---------------------------------------------------------------------------

class NextQuestionResponse(BaseModel):
    question_text: str
    theme: str
    question_type: str = Field(
        ..., description="One of: core | followup | clarification"
    )


# ---------------------------------------------------------------------------
# Final Recommendation
# ---------------------------------------------------------------------------

class FinalRecommendationResponse(BaseModel):
    label: str = Field(
        ..., description="One of: shortlist | hold | reject | needs_review"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    narrative_summary: str
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
