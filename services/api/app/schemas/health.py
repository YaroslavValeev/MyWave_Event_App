"""Health schemas."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    time: str
    db_ok: bool


class ReadyResponse(BaseModel):
    status: str
    db_ok: bool
