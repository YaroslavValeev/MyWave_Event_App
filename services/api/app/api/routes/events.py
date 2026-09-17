"""Event routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AppSettings, CurrentUser, DbSession, OptionalUser
from app.api.errors import raise_api_error
from app.schemas.event import EventCreate, EventListResponse, EventRead, EventUpdateStatus, RosterLockRequest
from app.services.event_service import (
    EventServiceError,
    create_event,
    get_event,
    list_events,
    lock_event_roster,
    unlock_event_roster,
    update_event_status,
)

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


@router.post("/{event_id}/roster/lock", response_model=EventRead)
def lock_roster_route(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    body: RosterLockRequest = RosterLockRequest(),
) -> EventRead:
    try:
        event = lock_event_roster(
            db,
            event_id=event_id,
            actor=user,
            reason=body.reason,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return EventRead.model_validate(event)


@router.post("/{event_id}/roster/unlock", response_model=EventRead)
def unlock_roster_route(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    body: RosterLockRequest = RosterLockRequest(),
) -> EventRead:
    try:
        event = unlock_event_roster(
            db,
            event_id=event_id,
            actor=user,
            reason=body.reason,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return EventRead.model_validate(event)
