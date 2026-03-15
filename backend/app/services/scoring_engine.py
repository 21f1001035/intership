from __future__ import annotations

import logging
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.interview import InterviewTheme
from app.models.scoring import InterviewScore
from app.schemas.llm import AnswerEvaluation

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Maintains a running per-dimension score for each application.
    Each time an answer is evaluated by the LLM, the relevant dimension's
    score is updated using an exponential running average (equal weighting
    across multiple evaluations for simplicity in v1).
    """

    THEME_TO_DIMENSION: Dict[str, str] = {
        InterviewTheme.MOTIVATION.value: "motivation_score",
        InterviewTheme.PROJECT_DEEP_DIVE.value: "project_depth_score",
        InterviewTheme.ML_FUNDAMENTALS.value: "ml_understanding_score",
        InterviewTheme.CODING_DEPTH.value: "coding_maturity_score",
        InterviewTheme.AVAILABILITY.value: "completeness_score",
    }

    # Weights must sum to 1.0 across all scored dimensions
    WEIGHTS: Dict[str, float] = {
        "technical_foundation_score": 0.15,
        "project_depth_score": 0.20,
        "ml_understanding_score": 0.20,
        "coding_maturity_score": 0.15,
        "communication_score": 0.10,
        "motivation_score": 0.10,
        "completeness_score": 0.10,
    }

    def update_score_from_evaluation(
        self,
        application_id: UUID,
        theme: InterviewTheme,
        evaluation: AnswerEvaluation,
        db: Session,
    ) -> InterviewScore:
        """
        Update (or create) the InterviewScore for the given application based
        on a single AnswerEvaluation. Uses a simple running average per dimension.

        Returns the updated InterviewScore ORM object (not yet committed).
        """
        score_record = (
            db.query(InterviewScore)
            .filter(InterviewScore.application_id == application_id)
            .first()
        )
        if score_record is None:
            score_record = InterviewScore(application_id=application_id)
            db.add(score_record)

        dimension = self.THEME_TO_DIMENSION.get(theme.value)
        if dimension:
            current = getattr(score_record, dimension)
            new_score = float(evaluation.score)
            if current is None:
                updated = new_score
            else:
                # Simple average of previous value and new evaluation
                updated = round((current + new_score) / 2.0, 2)
            setattr(score_record, dimension, updated)
            logger.debug(
                "Score updated",
                application_id=str(application_id),
                dimension=dimension,
                old=current,
                new=updated,
            )

        # Also update communication score heuristically based on answer quality
        comm_map = {"strong": 8.5, "adequate": 6.0, "vague": 3.5, "off_topic": 2.0}
        comm_contribution = comm_map.get(evaluation.quality, 5.0)
        if score_record.communication_score is None:
            score_record.communication_score = round(comm_contribution, 2)
        else:
            score_record.communication_score = round(
                (score_record.communication_score + comm_contribution) / 2.0, 2
            )

        # Recompute overall weighted score from all available dimensions
        score_record.overall_score = self._compute_overall(score_record)

        db.flush()
        return score_record

    def _compute_overall(self, score_record: InterviewScore) -> Optional[float]:
        """
        Compute a weighted overall score from the dimensions that have been scored.
        Dimensions that are still None are excluded from both numerator and denominator.
        """
        numerator = 0.0
        denominator = 0.0
        for dim, weight in self.WEIGHTS.items():
            value = getattr(score_record, dim, None)
            if value is not None:
                numerator += value * weight
                denominator += weight

        if denominator == 0.0:
            return None
        return round(numerator / denominator, 2)
