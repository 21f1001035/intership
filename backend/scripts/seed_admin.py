"""
Seed the initial admin user into the database.

Usage (from the backend/ directory):
    python -m scripts.seed_admin
"""
from __future__ import annotations

import sys
import os

# Ensure the backend package is on sys.path when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin import AdminUser


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(AdminUser.email == settings.ADMIN_EMAIL).first()
        if existing:
            print(f"Admin user already exists: {settings.ADMIN_EMAIL}")
            return

        admin = AdminUser(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            full_name="Admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin user created successfully: {settings.ADMIN_EMAIL}")
    except Exception as exc:
        db.rollback()
        print(f"ERROR: Failed to seed admin user: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
