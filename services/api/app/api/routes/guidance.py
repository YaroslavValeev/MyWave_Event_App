"""Journey guidance API — ADR-0015."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession, OptionalUser
from app.api.errors import raise_api_error
from app.services.event_service import EventServiceError
from app.services.guidance_service import build_guidance

router = APIRouter(prefix="/events", tags=["guidance"])


@router.get("/{event_id}/guidance")
def get_guidance(event_id: int, db: DbSession, user: OptionalUser) -> dict:
    try:
        return build_guidance(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
