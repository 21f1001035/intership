from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    entity_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # e.g. "application", "interview_session"
    entity_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )  # UUID or other identifier as string
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # e.g. "status_change", "resume_uploaded"
    actor_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "student" | "admin" | "system"
    actor_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # admin UUID or student UUID as string
    payload_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} entity={self.entity_type}:{self.entity_id} "
            f"action={self.action}>"
        )
