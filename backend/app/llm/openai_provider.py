from __future__ import annotations

import json
import structlog
from typing import Any, Dict

from openai import AzureOpenAI, OpenAIError

from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.prompts.answer_evaluation import (
    ANSWER_EVALUATION_SYSTEM,
    ANSWER_EVALUATION_USER,
)
from app.llm.prompts.final_recommendation import (
    FINAL_RECOMMENDATION_SYSTEM,
    FINAL_RECOMMENDATION_USER,
)
from app.llm.prompts.next_question import NEXT_QUESTION_SYSTEM, NEXT_QUESTION_USER
from app.llm.prompts.resume_normalization import (
    RESUME_NORMALIZATION_SYSTEM,
    RESUME_NORMALIZATION_USER,
)
from app.schemas.llm import (
    AnswerEvaluation,
    FinalRecommendationResponse,
    NextQuestionResponse,
    ResumeStructuredProfile,
)

logger = structlog.get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """
    Production LLM provider backed by OpenAI Chat Completions API.
    All calls use response_format={"type": "json_object"} to guarantee
    parseable output.
    """

    def __init__(self, deployment: str | None = None) -> None:
        self._client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        # deployment name is the Azure resource name (e.g. "gpt-4o-mini")
        self._model = deployment or settings.AZURE_DEPLOYMENT_GPT4OMINI

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request and return the parsed JSON dict.
        Raises RuntimeError on LLM / parse failures so callers can handle them.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content or "{}"
            return json.loads(raw_content)
        except OpenAIError as exc:
            logger.error("OpenAI API error", exc_info=exc)
            raise RuntimeError(f"OpenAI API error: {exc}") from exc
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM JSON response", exc_info=exc)
            raise RuntimeError(f"LLM returned non-JSON output: {exc}") from exc

    # ------------------------------------------------------------------
    # LLMProvider implementation
    # ------------------------------------------------------------------

    def normalize_resume(self, raw_text: str) -> ResumeStructuredProfile:
        """Parse raw resume text into a ResumeStructuredProfile."""
        logger.info("Calling LLM for resume normalization", extra={"model": self._model})
        user_prompt = RESUME_NORMALIZATION_USER.format(raw_text=raw_text)
        data = self._chat_json(
            system_prompt=RESUME_NORMALIZATION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=3000,
        )
        try:
            return ResumeStructuredProfile(**data)
        except Exception as exc:
            logger.warning(
                "Resume profile validation failed, returning partial data",
                exc_info=exc,
            )
            # Return whatever we can parse rather than failing entirely
            return ResumeStructuredProfile.model_validate(data, strict=False)

    def evaluate_answer(self, context: Dict[str, Any]) -> AnswerEvaluation:
        """Evaluate a student's interview answer."""
        logger.info(
            "Calling LLM for answer evaluation",
            extra={"theme": context.get("theme"), "model": self._model},
        )
        user_prompt = ANSWER_EVALUATION_USER.format(
            theme=context.get("theme", ""),
            question=context.get("question", ""),
            answer=context.get("answer", ""),
            context_summary=context.get("context_summary", "None"),
            profile_highlights=context.get("profile_highlights", "Not available"),
            followups_used=context.get("followups_used", 0),
            max_followups=context.get("max_followups", settings.INTERVIEW_MAX_FOLLOWUPS_PER_THEME),
        )
        data = self._chat_json(
            system_prompt=ANSWER_EVALUATION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=1024,
        )
        try:
            return AnswerEvaluation(**data)
        except Exception as exc:
            logger.error("AnswerEvaluation parse failed", exc_info=exc)
            # Safe fallback: treat as adequate, move on
            return AnswerEvaluation(
                theme=context.get("theme", "unknown"),
                quality="adequate",
                score=5.0,
                reasoning="Evaluation unavailable due to parsing error.",
                follow_up_needed=False,
                follow_up_question=None,
                move_to_next_theme=True,
            )

    def generate_next_question(self, context: Dict[str, Any]) -> NextQuestionResponse:
        """Generate the next interview question."""
        logger.info(
            "Calling LLM for next question",
            extra={
                "theme": context.get("theme"),
                "question_type": context.get("question_type"),
                "model": self._model,
            },
        )
        user_prompt = NEXT_QUESTION_USER.format(
            theme=context.get("theme", ""),
            question_type=context.get("question_type", "core"),
            profile_summary=context.get("profile_summary", "Not available"),
            conversation_history=context.get("conversation_history", "None"),
        )
        data = self._chat_json(
            system_prompt=NEXT_QUESTION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=512,
        )
        try:
            return NextQuestionResponse(**data)
        except Exception as exc:
            logger.error("NextQuestionResponse parse failed", exc_info=exc)
            theme = context.get("theme", "motivation")
            return NextQuestionResponse(
                question_text=(
                    "Could you tell me more about your background in AI and machine learning?"
                ),
                theme=theme,
                question_type="core",
            )

    def generate_final_recommendation(
        self, context: Dict[str, Any]
    ) -> FinalRecommendationResponse:
        """Generate the final hire/no-hire recommendation."""
        logger.info(
            "Calling LLM for final recommendation",
            extra={"candidate": context.get("candidate_name"), "model": self._model},
        )
        user_prompt = FINAL_RECOMMENDATION_USER.format(
            candidate_name=context.get("candidate_name", "Unknown"),
            college=context.get("college", "Unknown"),
            degree=context.get("degree", "B.Tech"),
            branch=context.get("branch", "Unknown"),
            year=context.get("year", "Unknown"),
            cgpa=context.get("cgpa", "Not provided"),
            profile_json=context.get("profile_json", "{}"),
            transcript_summary=context.get("transcript_summary", "Not available"),
            technical_foundation_score=context.get("technical_foundation_score", "N/A"),
            project_depth_score=context.get("project_depth_score", "N/A"),
            ml_understanding_score=context.get("ml_understanding_score", "N/A"),
            coding_maturity_score=context.get("coding_maturity_score", "N/A"),
            communication_score=context.get("communication_score", "N/A"),
            motivation_score=context.get("motivation_score", "N/A"),
            completeness_score=context.get("completeness_score", "N/A"),
            authenticity_flag=context.get("authenticity_flag", False),
        )
        data = self._chat_json(
            system_prompt=FINAL_RECOMMENDATION_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=1500,
        )
        try:
            return FinalRecommendationResponse(**data)
        except Exception as exc:
            logger.error("FinalRecommendationResponse parse failed", exc_info=exc)
            return FinalRecommendationResponse(
                label="needs_review",
                confidence=0.5,
                rationale="Automated recommendation failed; manual review required.",
                narrative_summary="The automated scoring system encountered an error. Please review manually.",
                score_breakdown={},
            )
