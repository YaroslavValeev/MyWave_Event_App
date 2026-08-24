"""Event domain service."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.roles import EVENT_ADMIN_READ_ROLES, EVENT_WRITE_ROLES, Role
from app.models.event import Event, EventStatus
from app.models.user import User
from app.schemas.event import EventCreate, EventUpdateStatus
from app.services.audit_service import append_audit


class EventServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _role_of(user: User) -> Role:
    return Role(user.role)


def can_write_events(user: User) -> bool:
    return _role_of(user) in EVENT_WRITE_ROLES


def can_read_all_events(user: User) -> bool:
    return _role_of(user) in EVENT_ADMIN_READ_ROLES


def create_event(
    db: Session,
    *,
    data: EventCreate,
    actor: User,
    audit_enabled: bool = True,
) -> Event:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to create events", 403)

    event = Event(
        slug=data.slug,
        title=data.title,
        description=data.description,
        city=data.city,
        location=data.location,
        venue=data.venue,
        disciplines=data.disciplines,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        status=data.status.value,
    )
    db.add(event)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise EventServiceError("slug_taken", f"Event slug already exists: {data.slug}", 409) from exc

    append_audit(
        db,
        action="event.create",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event",
        entity_id=str(event.id),
        payload={"slug": event.slug, "status": event.status},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, *, actor: User) -> list[Event]:
    stmt = select(Event).order_by(Event.id.desc())
    if not can_read_all_events(actor):
        visible = [
            EventStatus.published.value,
            EventStatus.registration_open.value,
            EventStatus.live.value,
            EventStatus.completed.value,
        ]
        stmt = stmt.where(Event.status.in_(visible))
    return list(db.scalars(stmt).all())


def get_event(db: Session, *, event_id: int, actor: User) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise EventServiceError("not_found", "Event not found", 404)

    if not can_read_all_events(actor):
        visible = {
            EventStatus.published.value,
            EventStatus.registration_open.value,
            EventStatus.live.value,
            EventStatus.completed.value,
        }
        if event.status not in visible:
            raise EventServiceError("not_found", "Event not found", 404)
    return event


def update_event_status(
    db: Session,
    *,
    event_id: int,
    data: EventUpdateStatus,
    actor: User,
    audit_enabled: bool = True,
) -> Event:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to update events", 403)

    event = db.get(Event, event_id)
    if event is None:
        raise EventServiceError("not_found", "Event not found", 404)

    previous = event.status
    event.status = data.status.value
    db.add(event)
    db.flush()

    append_audit(
        db,
        action="event.update_status",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event",
        entity_id=str(event.id),
        payload={"from": previous, "to": event.status},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(event)
    return event


def count_events(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(Event)) or 0)
