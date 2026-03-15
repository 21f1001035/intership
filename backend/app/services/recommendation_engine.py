from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation, RecommendationLabel
from app.models.scoring import InterviewScore

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Rule-based fallback recommendation engine used when the LLM recommendation
    is unavailable or as a sanity-check layer on top of LLM output.
    """

    # Thresholds
    SHORTLIST_THRESHOLD = 7.0
    HOLD_THRESHOLD = 5.0

    def compute_rule_based_label(self, score_record: InterviewScore) -> RecommendationLabel:
        """
        Derive a recommendation label purely from score thresholds.
        Used as a fallback when LLM is unavailable.
        """
        if score_record.authenticity_flag:
            return RecommendationLabel.NEEDS_REVIEW

        overall = score_record.overall_score
        if overall is None:
            return RecommendationLabel.NEEDS_REVIEW

        if overall >= self.SHORTLIST_THRESHOLD:
            return RecommendationLabel.SHORTLIST
        elif overall >= self.HOLD_THRESHOLD:
            return RecommendationLabel.HOLD
        else:
            return RecommendationLabel.REJECT

    def get_or_create_recommendation(
        self, application_id: UUID, db: Session
    ) -> Recommendation:
        """Retrieve an existing recommendation or create an empty placeholder."""
        rec = (
            db.query(Recommendation)
            .filter(Recommendation.application_id == application_id)
            .first()
        )
        if rec is None:
            rec = Recommendation(
                application_id=application_id,
                label=RecommendationLabel.NEEDS_REVIEW,
                confidence=0.0,
            )
            db.add(rec)
            db.flush()
        return rec
