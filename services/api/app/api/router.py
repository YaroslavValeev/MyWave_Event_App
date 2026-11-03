"""Root API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    audit,
    auth,
    competition,
    consent,
    events,
    guidance,
    health,
    notifications,
    protocol_revisions,
    publications,
    rules,
    scoreboard,
)

api_router = APIRouter()
api_router.include_router(health.router)

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth.router)
v1_router.include_router(notifications.router)
v1_router.include_router(consent.router)
v1_router.include_router(events.router)
v1_router.include_router(rules.router)
v1_router.include_router(competition.router)
v1_router.include_router(publications.router)
v1_router.include_router(guidance.router)
v1_router.include_router(scoreboard.router)
v1_router.include_router(protocol_revisions.router)
v1_router.include_router(audit.router)
