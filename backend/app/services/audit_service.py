from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """
    Thin service for writing structured audit log entries.
    All writes are done within the caller's transaction (no autocommit).
    """

    def log(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
        action: str,
        actor_type: str,
        actor_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """
        Append an audit log entry to the current session.

        Args:
            db:          SQLAlchemy session (caller's transaction).
            entity_type: The type of object being acted on ("application", "interview_session", etc.)
            entity_id:   String representation of the entity's primary key.
            action:      What happened ("status_change", "resume_uploaded", "interview_started", etc.)
            actor_type:  Who/what performed the action: "student" | "admin" | "system".
            actor_id:    Optional UUID (as string) of the acting user.
            payload:     Optional dict of additional context (old/new values, etc.)
            ip_address:  Optional IP address of the request origin.

        Returns:
            The AuditLog ORM instance (not yet committed).
        """
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_type=actor_type,
            actor_id=actor_id,
            payload_json=payload or {},
            ip_address=ip_address,
        )
        db.add(entry)
        logger.debug(
            "Audit log entry created",
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_type=actor_type,
        )
        return entry
