"""Health and readiness routes."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.errors import error_payload
from app.config import get_settings
from app.db import check_db
from app.schemas.health import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    db_ok = check_db()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        app=settings.app_name,
        env=settings.app_env,
        time=datetime.now(timezone.utc).isoformat(),
        db_ok=db_ok,
    )


@router.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse | JSONResponse:
    db_ok = check_db()
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_payload("db_unavailable", "Database is not ready"),
        )
    return ReadyResponse(status="ready", db_ok=True)
