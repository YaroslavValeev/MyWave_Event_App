"""Root API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import audit, auth, competition, consent, events, health, notifications

api_router = APIRouter()
api_router.include_router(health.router)

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth.router)
v1_router.include_router(notifications.router)
v1_router.include_router(consent.router)
v1_router.include_router(events.router)
v1_router.include_router(competition.router)
v1_router.include_router(audit.router)
