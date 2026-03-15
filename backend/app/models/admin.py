from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.application import Application


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    notes: Mapped[List["ReviewerNote"]] = relationship(
        "ReviewerNote", back_populates="admin_user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AdminUser id={self.id} email={self.email}>"


class ReviewerNote(Base):
    __tablename__ = "reviewer_notes"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    application_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
        index=True,
    )
    admin_user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id"),
        nullable=False,
        index=True,
    )
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="reviewer_notes"
    )
    admin_user: Mapped["AdminUser"] = relationship(
        "AdminUser", back_populates="notes"
    )

    def __repr__(self) -> str:
        return f"<ReviewerNote id={self.id} app={self.application_id}>"
