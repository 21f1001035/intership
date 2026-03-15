"""Initial schema — all tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Create ENUM types first (PostgreSQL requires this before using them)
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE application_status AS ENUM (
                'received',
                'interview_in_progress',
                'completed',
                'shortlisted',
                'hold',
                'rejected',
                'needs_review'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
        """
    )

    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE interview_status AS ENUM (
                'not_started',
                'in_progress',
                'completed',
                'abandoned'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
        """
    )

    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE interview_theme AS ENUM (
                'motivation',
                'project_deep_dive',
                'ml_fundamentals',
                'coding_depth',
                'availability',
                'complete'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
        """
    )

    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE sender_type AS ENUM (
                'student',
                'bot',
                'system'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
        """
    )

    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE recommendation_label AS ENUM (
                'shortlist',
                'hold',
                'reject',
                'needs_review'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
        """
    )

    # ------------------------------------------------------------------
    # students
    # ------------------------------------------------------------------
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("college", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(100), nullable=False),
        sa.Column("branch", sa.String(100), nullable=False),
        sa.Column("year_of_study", sa.Integer(), nullable=False),
        sa.Column("cgpa", sa.Float(), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("github_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_students_email", "students", ["email"], unique=True)

    # ------------------------------------------------------------------
    # applications
    # ------------------------------------------------------------------
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("internship_track", sa.String(100), nullable=False, server_default="AI/ML"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "received",
                "interview_in_progress",
                "completed",
                "shortlisted",
                "hold",
                "rejected",
                "needs_review",
                name="application_status",
                create_type=False,
            ),
            nullable=False,
            server_default="received",
        ),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("statement_of_interest", sa.Text(), nullable=True),
        sa.Column("application_token", sa.String(64), nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_applications_student_id", "applications", ["student_id"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index(
        "ix_applications_application_token",
        "applications",
        ["application_token"],
        unique=True,
    )

    # ------------------------------------------------------------------
    # application_status_history
    # ------------------------------------------------------------------
    op.create_table(
        "application_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("old_status", sa.String(50), nullable=True),
        sa.Column("new_status", sa.String(50), nullable=False),
        sa.Column("changed_by", sa.String(255), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_application_status_history_application_id",
        "application_status_history",
        ["application_id"],
    )

    # ------------------------------------------------------------------
    # documents
    # ------------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False, server_default="resume"),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_documents_application_id", "documents", ["application_id"])

    # ------------------------------------------------------------------
    # resume_extractions
    # ------------------------------------------------------------------
    op.create_table(
        "resume_extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("structured_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("extraction_provider", sa.String(50), nullable=True),
        sa.Column("extraction_model", sa.String(100), nullable=True),
        sa.Column("extraction_version", sa.String(20), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id"),
    )
    op.create_index(
        "ix_resume_extractions_application_id",
        "resume_extractions",
        ["application_id"],
    )

    # ------------------------------------------------------------------
    # interview_sessions
    # ------------------------------------------------------------------
    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "session_status",
            postgresql.ENUM(
                "not_started",
                "in_progress",
                "completed",
                "abandoned",
                name="interview_status",
                create_type=False,
            ),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column(
            "current_theme",
            postgresql.ENUM(
                "motivation",
                "project_deep_dive",
                "ml_fundamentals",
                "coding_depth",
                "availability",
                "complete",
                name="interview_theme",
                create_type=False,
            ),
            nullable=False,
            server_default="motivation",
        ),
        sa.Column("turn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "followup_counts",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id"),
    )
    op.create_index(
        "ix_interview_sessions_application_id",
        "interview_sessions",
        ["application_id"],
    )
    op.create_index(
        "ix_interview_sessions_session_status",
        "interview_sessions",
        ["session_status"],
    )

    # ------------------------------------------------------------------
    # interview_messages
    # ------------------------------------------------------------------
    op.create_table(
        "interview_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "sender_type",
            postgresql.ENUM(
                "student",
                "bot",
                "system",
                name="sender_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column(
            "message_json",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("theme", sa.String(50), nullable=True),
        sa.Column("turn_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_interview_messages_session_id",
        "interview_messages",
        ["session_id"],
    )
    op.create_index(
        "ix_interview_messages_theme",
        "interview_messages",
        ["theme"],
    )

    # ------------------------------------------------------------------
    # interview_scores
    # ------------------------------------------------------------------
    op.create_table(
        "interview_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technical_foundation_score", sa.Float(), nullable=True),
        sa.Column("project_depth_score", sa.Float(), nullable=True),
        sa.Column("ml_understanding_score", sa.Float(), nullable=True),
        sa.Column("coding_maturity_score", sa.Float(), nullable=True),
        sa.Column("communication_score", sa.Float(), nullable=True),
        sa.Column("motivation_score", sa.Float(), nullable=True),
        sa.Column("completeness_score", sa.Float(), nullable=True),
        sa.Column("authenticity_flag", sa.Boolean(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column(
            "rationale_json",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("scoring_version", sa.String(20), nullable=True, server_default="1.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id"),
    )
    op.create_index(
        "ix_interview_scores_application_id",
        "interview_scores",
        ["application_id"],
    )

    # ------------------------------------------------------------------
    # recommendations
    # ------------------------------------------------------------------
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "label",
            postgresql.ENUM(
                "shortlist",
                "hold",
                "reject",
                "needs_review",
                name="recommendation_label",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("narrative_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id"),
    )
    op.create_index(
        "ix_recommendations_application_id",
        "recommendations",
        ["application_id"],
    )
    op.create_index(
        "ix_recommendations_label",
        "recommendations",
        ["label"],
    )

    # ------------------------------------------------------------------
    # admin_users
    # ------------------------------------------------------------------
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # reviewer_notes
    # ------------------------------------------------------------------
    op.create_table(
        "reviewer_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admin_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reviewer_notes_application_id",
        "reviewer_notes",
        ["application_id"],
    )
    op.create_index(
        "ix_reviewer_notes_admin_user_id",
        "reviewer_notes",
        ["admin_user_id"],
    )

    # ------------------------------------------------------------------
    # audit_logs
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("actor_type", sa.String(50), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=True),
        sa.Column(
            "payload_json",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("audit_logs")
    op.drop_table("reviewer_notes")
    op.drop_table("admin_users")
    op.drop_table("recommendations")
    op.drop_table("interview_scores")
    op.drop_table("interview_messages")
    op.drop_table("interview_sessions")
    op.drop_table("resume_extractions")
    op.drop_table("documents")
    op.drop_table("application_status_history")
    op.drop_table("applications")
    op.drop_table("students")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS recommendation_label")
    op.execute("DROP TYPE IF EXISTS sender_type")
    op.execute("DROP TYPE IF EXISTS interview_theme")
    op.execute("DROP TYPE IF EXISTS interview_status")
    op.execute("DROP TYPE IF EXISTS application_status")
