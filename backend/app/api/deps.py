from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.llm.base import LLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.models.admin import AdminUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

# Module-level singleton for the LLM provider (avoids re-creating the client per request)
_llm_provider: LLMProvider | None = None


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and ensure it is closed afterwards."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_llm_provider() -> LLMProvider:
    """
    Return a shared LLMProvider instance (OpenAI backed).
    The provider is instantiated once per process.
    """
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = OpenAIProvider()
    return _llm_provider


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    """
    FastAPI dependency that decodes the JWT bearer token and returns the
    corresponding AdminUser. Raises HTTP 401 if the token is invalid, expired,
    or the user does not exist / is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    admin_id: str | None = payload.get("sub")
    if admin_id is None:
        raise credentials_exception

    admin = db.query(AdminUser).filter(AdminUser.email == admin_id).first()
    if admin is None or not admin.is_active:
        raise credentials_exception

    return admin
