"""Event routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AppSettings, CurrentUser, DbSession, OptionalUser
from app.api.errors import raise_api_error
from app.schemas.event import EventCreate, EventListResponse, EventRead, EventUpdateStatus
from app.services.event_service import EventServiceError, create_event, get_event, list_events, update_event_status

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=201)
def create_event_route(
    body: EventCreate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> EventRead:
    try:
        event = create_event(db, data=body, actor=user, audit_enabled=settings.enable_audit_log)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return EventRead.model_validate(event)


@router.get("", response_model=EventListResponse)
def list_events_route(db: DbSession, user: OptionalUser) -> EventListResponse:
    items = list_events(db, actor=user)
    return EventListResponse(items=[EventRead.model_validate(e) for e in items], total=len(items))


@router.get("/{event_id}", response_model=EventRead)
def get_event_route(event_id: int, db: DbSession, user: OptionalUser) -> EventRead:
    try:
        event = get_event(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return EventRead.model_validate(event)


@router.patch("/{event_id}/status", response_model=EventRead)
def update_event_status_route(
    event_id: int,
    body: EventUpdateStatus,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> EventRead:
    try:
        event = update_event_status(
            db,
            event_id=event_id,
            data=body,
            actor=user,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return EventRead.model_validate(event)
