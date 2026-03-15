from __future__ import annotations

import json
import structlog
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, settings as default_settings
from app.llm.base import LLMProvider
from app.models.application import Application, ApplicationStatus
from app.models.interview import (
    InterviewMessage,
    InterviewSession,
    InterviewStatus,
    InterviewTheme,
    SenderType,
)
from app.models.recommendation import Recommendation, RecommendationLabel
from app.models.scoring import InterviewScore
from app.services.audit_service import AuditService
from app.services.scoring_engine import ScoringEngine

logger = structlog.get_logger(__name__)

# Ordered list of themes — must complete all before the interview is finalised
THEME_ORDER: List[InterviewTheme] = [
    InterviewTheme.MOTIVATION,
    InterviewTheme.PROJECT_DEEP_DIVE,
    InterviewTheme.ML_FUNDAMENTALS,
    InterviewTheme.CODING_DEPTH,
    InterviewTheme.AVAILABILITY,
]

_audit = AuditService()
_scoring = ScoringEngine()


class InterviewOrchestrator:
    """
    Manages the full lifecycle of a single AI/ML internship interview:
    - Starting the session
    - Processing each student message
    - Advancing through themes
    - Finalising and generating a recommendation
    """

    def __init__(
        self,
        db: Session,
        llm_provider: LLMProvider,
        app_settings: Optional[Settings] = None,
    ) -> None:
        self.db = db
        self.llm = llm_provider
        self.settings = app_settings or default_settings

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_interview(
        self, application_id: UUID
    ) -> Tuple[InterviewSession, InterviewMessage]:
        """
        Initialise a new interview session and return the first bot question.

        Raises:
            ValueError: if the application is not found or is not in a startable state.
        """
        application = self._get_application_or_raise(application_id)

        # Guard: only allow starting if application has a resume and is in RECEIVED or
        # INTERVIEW_IN_PROGRESS (idempotent restart for in-progress)
        if application.status not in (
            ApplicationStatus.RECEIVED,
            ApplicationStatus.INTERVIEW_IN_PROGRESS,
        ):
            raise ValueError(
                f"Application {application_id} is in status '{application.status.value}' "
                "and cannot start/restart an interview."
            )

        # Guard: no duplicate active session
        existing_session = (
            self.db.query(InterviewSession)
            .filter(InterviewSession.application_id == application_id)
            .filter(InterviewSession.session_status == InterviewStatus.IN_PROGRESS)
            .first()
        )
        if existing_session:
            raise ValueError(
                f"An active interview session already exists for application {application_id}."
            )

        # Create session
        session = InterviewSession(
            application_id=application_id,
            session_status=InterviewStatus.IN_PROGRESS,
            current_theme=InterviewTheme.MOTIVATION,
            turn_count=0,
            followup_counts={theme.value: 0 for theme in THEME_ORDER},
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        self.db.flush()  # get the session.id

        # Update application status
        application.status = ApplicationStatus.INTERVIEW_IN_PROGRESS
        self.db.flush()

        # Build context for the first question
        profile_summary = self._get_profile_summary(application)
        context = {
            "theme": InterviewTheme.MOTIVATION.value,
            "question_type": "core",
            "profile_summary": profile_summary,
            "conversation_history": "This is the start of the interview.",
        }

        first_q = self.llm.generate_next_question(context)

        # Store the bot message
        bot_msg = InterviewMessage(
            session_id=session.id,
            sender_type=SenderType.BOT,
            message_text=first_q.question_text,
            message_json={"question_type": first_q.question_type},
            theme=first_q.theme,
            turn_number=0,
        )
        self.db.add(bot_msg)

        _audit.log(
            db=self.db,
            entity_type="interview_session",
            entity_id=str(session.id),
            action="interview_started",
            actor_type="system",
            payload={"application_id": str(application_id)},
        )

        self.db.flush()
        logger.info(
            "Interview started",
            application_id=str(application_id),
            session_id=str(session.id),
        )
        return session, bot_msg

    def process_student_message(
        self, session_id: UUID, message_text: str
    ) -> Tuple[InterviewSession, InterviewMessage]:
        """
        Handle a student reply:
        1. Persist the student message.
        2. Evaluate the answer via LLM.
        3. Update running scores.
        4. Determine next action (follow-up / advance theme / finalise).
        5. Generate and persist the bot's next message.

        Returns (session, bot_message).
        """
        session = self._get_session_or_raise(session_id)

        if session.session_status != InterviewStatus.IN_PROGRESS:
            raise ValueError(
                f"Session {session_id} is not in progress "
                f"(current status: {session.session_status.value})."
            )

        application = self._get_application_or_raise(session.application_id)

        # ---- 1. Persist the student's message ----
        session.turn_count = (session.turn_count or 0) + 1
        student_msg = InterviewMessage(
            session_id=session.id,
            sender_type=SenderType.STUDENT,
            message_text=message_text,
            theme=session.current_theme.value,
            turn_number=session.turn_count,
        )
        self.db.add(student_msg)
        self.db.flush()

        # ---- 2. Retrieve the last bot question for context ----
        last_bot_question = (
            self.db.query(InterviewMessage)
            .filter(
                InterviewMessage.session_id == session_id,
                InterviewMessage.sender_type == SenderType.BOT,
            )
            .order_by(InterviewMessage.turn_number.desc())
            .first()
        )
        last_question_text = (
            last_bot_question.message_text if last_bot_question else "No prior question"
        )

        # ---- 3. Evaluate the answer ----
        followup_counts: Dict[str, int] = session.followup_counts or {}
        theme_key = session.current_theme.value
        followups_used = followup_counts.get(theme_key, 0)
        max_followups = self.settings.INTERVIEW_MAX_FOLLOWUPS_PER_THEME

        eval_context = {
            "theme": session.current_theme.value,
            "question": last_question_text,
            "answer": message_text,
            "context_summary": self._build_conversation_summary(session),
            "profile_highlights": self._get_profile_summary(application),
            "followups_used": followups_used,
            "max_followups": max_followups,
        }
        evaluation = self.llm.evaluate_answer(eval_context)

        # Persist evaluation metadata on the student message
        student_msg.message_json = {
            "quality": evaluation.quality,
            "score": evaluation.score,
            "reasoning": evaluation.reasoning,
        }

        # ---- 4. Update scores ----
        _scoring.update_score_from_evaluation(
            application_id=application.id,
            theme=session.current_theme,
            evaluation=evaluation,
            db=self.db,
        )

        # ---- 5. Determine next action ----
        max_turns_reached = session.turn_count >= self.settings.INTERVIEW_MAX_TURNS

        if max_turns_reached:
            logger.info(
                "Max turns reached, finalising interview",
                session_id=str(session_id),
                turns=session.turn_count,
            )
            bot_msg = self._finalise_interview_and_notify(session, application)
            return session, bot_msg

        if evaluation.move_to_next_theme or followups_used >= max_followups:
            next_theme = self._advance_theme(session)
            if next_theme == InterviewTheme.COMPLETE:
                bot_msg = self._finalise_interview_and_notify(session, application)
                return session, bot_msg
            # Generate core question for new theme
            bot_msg = self._generate_and_store_question(
                session=session,
                application=application,
                question_type="core",
            )
        elif evaluation.follow_up_needed and evaluation.follow_up_question:
            # Use LLM-provided follow-up question directly
            followup_counts[theme_key] = followups_used + 1
            session.followup_counts = followup_counts
            bot_msg = InterviewMessage(
                session_id=session.id,
                sender_type=SenderType.BOT,
                message_text=evaluation.follow_up_question,
                message_json={"question_type": "followup"},
                theme=session.current_theme.value,
                turn_number=session.turn_count,
            )
            self.db.add(bot_msg)
        else:
            # Adequate answer — move to next theme
            next_theme = self._advance_theme(session)
            if next_theme == InterviewTheme.COMPLETE:
                bot_msg = self._finalise_interview_and_notify(session, application)
                return session, bot_msg
            bot_msg = self._generate_and_store_question(
                session=session,
                application=application,
                question_type="core",
            )

        self.db.flush()
        return session, bot_msg

    def get_interview_state(self, application_id: UUID) -> Dict[str, Any]:
        """
        Return a serialisable snapshot of the interview state for the given application.
        """
        application = self._get_application_or_raise(application_id)

        session = (
            self.db.query(InterviewSession)
            .filter(InterviewSession.application_id == application_id)
            .first()
        )
        if session is None:
            return {
                "session": None,
                "messages": [],
                "scores": None,
                "is_complete": False,
            }

        messages = (
            self.db.query(InterviewMessage)
            .filter(InterviewMessage.session_id == session.id)
            .order_by(InterviewMessage.turn_number)
            .all()
        )

        scores = (
            self.db.query(InterviewScore)
            .filter(InterviewScore.application_id == application_id)
            .first()
        )

        return {
            "session": session,
            "messages": messages,
            "scores": scores,
            "is_complete": session.session_status == InterviewStatus.COMPLETED,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_application_or_raise(self, application_id: UUID) -> Application:
        application = (
            self.db.query(Application)
            .filter(Application.id == application_id)
            .first()
        )
        if application is None:
            raise ValueError(f"Application {application_id} not found.")
        return application

    def _get_session_or_raise(self, session_id: UUID) -> InterviewSession:
        session = (
            self.db.query(InterviewSession)
            .filter(InterviewSession.id == session_id)
            .first()
        )
        if session is None:
            raise ValueError(f"Interview session {session_id} not found.")
        return session

    def _advance_theme(self, session: InterviewSession) -> InterviewTheme:
        """Move to the next theme. Sets session.current_theme and returns the new theme."""
        try:
            current_index = THEME_ORDER.index(session.current_theme)
        except ValueError:
            return InterviewTheme.COMPLETE

        next_index = current_index + 1
        if next_index >= len(THEME_ORDER):
            session.current_theme = InterviewTheme.COMPLETE
            return InterviewTheme.COMPLETE

        next_theme = THEME_ORDER[next_index]
        session.current_theme = next_theme
        logger.info(
            "Theme advanced",
            session_id=str(session.id),
            from_theme=THEME_ORDER[current_index].value,
            to_theme=next_theme.value,
        )
        return next_theme

    def _generate_and_store_question(
        self,
        session: InterviewSession,
        application: Application,
        question_type: str = "core",
    ) -> InterviewMessage:
        """Ask the LLM for a question and persist it as a bot message."""
        context = {
            "theme": session.current_theme.value,
            "question_type": question_type,
            "profile_summary": self._get_profile_summary(application),
            "conversation_history": self._build_conversation_summary(session),
        }
        next_q = self.llm.generate_next_question(context)
        bot_msg = InterviewMessage(
            session_id=session.id,
            sender_type=SenderType.BOT,
            message_text=next_q.question_text,
            message_json={"question_type": next_q.question_type},
            theme=next_q.theme,
            turn_number=session.turn_count,
        )
        self.db.add(bot_msg)
        return bot_msg

    def _finalise_interview_and_notify(
        self, session: InterviewSession, application: Application
    ) -> InterviewMessage:
        """Finalise the interview and return a closing bot message."""
        self._finalise_interview(session, application)
        closing_text = (
            "Thank you for completing the interview! "
            "We will review your responses and get back to you shortly. "
            "Good luck!"
        )
        close_msg = InterviewMessage(
            session_id=session.id,
            sender_type=SenderType.BOT,
            message_text=closing_text,
            message_json={"question_type": "closing"},
            theme=InterviewTheme.COMPLETE.value,
            turn_number=session.turn_count,
        )
        self.db.add(close_msg)
        return close_msg

    def _finalise_interview(
        self, session: InterviewSession, application: Application
    ) -> None:
        """
        Mark interview complete, generate LLM recommendation, update application status.
        """
        session.session_status = InterviewStatus.COMPLETED
        session.ended_at = datetime.now(timezone.utc)
        session.current_theme = InterviewTheme.COMPLETE

        # Gather scores
        score_record = (
            self.db.query(InterviewScore)
            .filter(InterviewScore.application_id == application.id)
            .first()
        )

        # Build recommendation context
        student = application.student
        extraction = application.resume_extraction
        profile_json = json.dumps(extraction.structured_json or {}, indent=2) if extraction else "{}"

        transcript_summary = self._build_full_transcript_summary(session)

        rec_context = {
            "candidate_name": student.full_name if student else "Unknown",
            "college": student.college if student else "Unknown",
            "degree": student.degree if student else "Unknown",
            "branch": student.branch if student else "Unknown",
            "year": student.year_of_study if student else "Unknown",
            "cgpa": str(student.cgpa) if student and student.cgpa else "Not provided",
            "profile_json": profile_json,
            "transcript_summary": transcript_summary,
            "technical_foundation_score": score_record.technical_foundation_score if score_record else "N/A",
            "project_depth_score": score_record.project_depth_score if score_record else "N/A",
            "ml_understanding_score": score_record.ml_understanding_score if score_record else "N/A",
            "coding_maturity_score": score_record.coding_maturity_score if score_record else "N/A",
            "communication_score": score_record.communication_score if score_record else "N/A",
            "motivation_score": score_record.motivation_score if score_record else "N/A",
            "completeness_score": score_record.completeness_score if score_record else "N/A",
            "authenticity_flag": score_record.authenticity_flag if score_record else False,
        }

        try:
            rec_response = self.llm.generate_final_recommendation(rec_context)
        except Exception as exc:
            logger.error("Final recommendation LLM call failed", exc_info=exc)
            rec_response = None

        # Upsert Recommendation
        recommendation = (
            self.db.query(Recommendation)
            .filter(Recommendation.application_id == application.id)
            .first()
        )
        if recommendation is None:
            recommendation = Recommendation(application_id=application.id)
            self.db.add(recommendation)

        if rec_response:
            label_map = {
                "shortlist": RecommendationLabel.SHORTLIST,
                "hold": RecommendationLabel.HOLD,
                "reject": RecommendationLabel.REJECT,
                "needs_review": RecommendationLabel.NEEDS_REVIEW,
            }
            recommendation.label = label_map.get(
                rec_response.label, RecommendationLabel.NEEDS_REVIEW
            )
            recommendation.confidence = rec_response.confidence
            recommendation.rationale = rec_response.rationale
            recommendation.narrative_summary = rec_response.narrative_summary

            # Map recommendation label to application status
            status_map = {
                RecommendationLabel.SHORTLIST: ApplicationStatus.SHORTLISTED,
                RecommendationLabel.HOLD: ApplicationStatus.HOLD,
                RecommendationLabel.REJECT: ApplicationStatus.REJECTED,
                RecommendationLabel.NEEDS_REVIEW: ApplicationStatus.NEEDS_REVIEW,
            }
            application.status = status_map.get(
                recommendation.label, ApplicationStatus.COMPLETED
            )
        else:
            recommendation.label = RecommendationLabel.NEEDS_REVIEW
            recommendation.confidence = 0.0
            recommendation.rationale = "Automated recommendation unavailable."
            recommendation.narrative_summary = "Please review manually."
            application.status = ApplicationStatus.COMPLETED

        application.completed_at = datetime.now(timezone.utc)

        _audit.log(
            db=self.db,
            entity_type="interview_session",
            entity_id=str(session.id),
            action="interview_completed",
            actor_type="system",
            payload={
                "application_id": str(application.id),
                "recommendation_label": recommendation.label.value if recommendation.label else None,
                "overall_score": score_record.overall_score if score_record else None,
            },
        )
        self.db.flush()
        logger.info(
            "Interview finalised",
            session_id=str(session.id),
            application_id=str(application.id),
            recommendation=recommendation.label.value if recommendation.label else None,
        )

    def _get_profile_summary(self, application: Application) -> str:
        """Return a compact text summary of the candidate's profile."""
        student = application.student
        if not student:
            return "Candidate profile not available."

        lines = [
            f"Name: {student.full_name}",
            f"College: {student.college}",
            f"Degree: {student.degree} in {student.branch}, Year {student.year_of_study}",
        ]
        if student.cgpa:
            lines.append(f"CGPA: {student.cgpa}")

        extraction = application.resume_extraction
        if extraction and extraction.structured_json:
            sj = extraction.structured_json
            skills = sj.get("technical_skills", [])
            if skills:
                lines.append(f"Technical Skills: {', '.join(skills[:10])}")
            projects = sj.get("projects", [])
            if projects:
                titles = [p.get("title", "Untitled") for p in projects[:3]]
                lines.append(f"Notable Projects: {', '.join(titles)}")
            strengths = sj.get("inferred_strengths", [])
            if strengths:
                lines.append(f"Inferred Strengths: {', '.join(strengths[:3])}")

        return "\n".join(lines)

    def _build_conversation_summary(self, session: InterviewSession) -> str:
        """Return a compact text summary of the last few exchanges in the session."""
        messages = (
            self.db.query(InterviewMessage)
            .filter(InterviewMessage.session_id == session.id)
            .order_by(InterviewMessage.turn_number.desc())
            .limit(6)
            .all()
        )
        if not messages:
            return "No prior conversation."
        # Reverse to chronological order
        messages = list(reversed(messages))
        lines = []
        for msg in messages:
            sender = "Interviewer" if msg.sender_type == SenderType.BOT else "Candidate"
            lines.append(f"{sender}: {msg.message_text[:300]}")
        return "\n".join(lines)

    def _build_full_transcript_summary(self, session: InterviewSession) -> str:
        """Return the entire interview transcript as a readable string (truncated for LLM)."""
        messages = (
            self.db.query(InterviewMessage)
            .filter(InterviewMessage.session_id == session.id)
            .order_by(InterviewMessage.turn_number)
            .all()
        )
        if not messages:
            return "No transcript available."
        lines = []
        for msg in messages:
            sender = "Interviewer" if msg.sender_type == SenderType.BOT else "Candidate"
            theme_tag = f"[{msg.theme}] " if msg.theme else ""
            lines.append(f"{theme_tag}{sender}: {msg.message_text[:500]}")
        # Keep total under ~6000 chars to avoid token overruns
        full = "\n".join(lines)
        if len(full) > 6000:
            full = full[:6000] + "\n... [truncated]"
        return full
