from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from app.schemas.llm import (
    AnswerEvaluation,
    FinalRecommendationResponse,
    NextQuestionResponse,
    ResumeStructuredProfile,
)


class LLMProvider(ABC):
    """Abstract interface for LLM operations used in the screening pipeline."""

    @abstractmethod
    def normalize_resume(self, raw_text: str) -> ResumeStructuredProfile:
        """
        Parse raw resume text into a structured profile.

        Args:
            raw_text: Full plaintext extracted from the resume PDF.

        Returns:
            ResumeStructuredProfile with all extracted fields.
        """

    @abstractmethod
    def evaluate_answer(self, context: Dict[str, Any]) -> AnswerEvaluation:
        """
        Evaluate a student's answer to an interview question.

        Args:
            context: Dict containing keys:
                - theme (str)
                - question (str)
                - answer (str)
                - context_summary (str)
                - profile_highlights (str)
                - followups_used (int)
                - max_followups (int)

        Returns:
            AnswerEvaluation with quality, score, and next-action guidance.
        """

    @abstractmethod
    def generate_next_question(self, context: Dict[str, Any]) -> NextQuestionResponse:
        """
        Generate the next interview question given the current state.

        Args:
            context: Dict containing keys:
                - theme (str)
                - question_type (str) — "core" | "followup" | "clarification"
                - profile_summary (str)
                - conversation_history (str)

        Returns:
            NextQuestionResponse with the question text and metadata.
        """

    @abstractmethod
    def generate_final_recommendation(
        self, context: Dict[str, Any]
    ) -> FinalRecommendationResponse:
        """
        Generate a final hire/no-hire recommendation after the interview concludes.

        Args:
            context: Dict containing candidate info, scores, transcript summary, etc.

        Returns:
            FinalRecommendationResponse with label, confidence, rationale, and summary.
        """
