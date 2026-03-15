from __future__ import annotations

import structlog

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, applications, interview
from app.core.config import settings
from app.core.logging import configure_logging

# Configure logging before anything else
configure_logging()

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="IIT Ropar Screening Bot",
    description=(
        "Backend API for the IIT Ropar AI/ML internship screening system. "
        "Manages applications, automated interviews, scoring, and admin workflows."
    ),
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(applications.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"], summary="Health check")
def health() -> dict:
    """Simple health-check endpoint used by load balancers and monitoring."""
    return {"status": "ok", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Startup / shutdown events
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "IIT Ropar Screening Bot starting up | env=%s model=%s",
        settings.APP_ENV,
        settings.AZURE_DEPLOYMENT_GPT4OMINI,
    )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("IIT Ropar Screening Bot shutting down")
