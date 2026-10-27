"""Event domain service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.roles import (
    EVENT_ADMIN_READ_ROLES,
    EVENT_WRITE_ROLES,
    ROSTER_LOCK_ROLES,
    Role,
)
from app.models.event import Event, EventStatus
from app.models.participant import Participant
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


ARCHIVED_EVENT_STATUSES = frozenset(
    {
        EventStatus.completed.value,
        EventStatus.cancelled.value,
    }
)


def is_event_archived(event: Event) -> bool:
    return event.status in ARCHIVED_EVENT_STATUSES


def assert_event_mutable(event: Event) -> None:
    """Block mutations on completed/cancelled events (read-only archive)."""
    if is_event_archived(event):
        raise EventServiceError(
            "event_archived",
            "Событие завершено или отменено и доступно только для чтения",
            409,
        )


def is_roster_locked(event: Event) -> bool:
    return event.roster_locked_at is not None


def assert_roster_unlocked(event: Event) -> None:
    """Block roster mutations after organizer lock."""
    if is_roster_locked(event):
        raise EventServiceError(
            "roster_locked",
            "Состав события зафиксирован. Новые заявки и импорт состава недоступны.",
            409,
        )


def _can_lock_roster(user: User) -> bool:
    return _role_of(user) in ROSTER_LOCK_ROLES


def _accepted_roster_count(db: Session, event_id: int) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Participant)
            .where(
                Participant.event_id == event_id,
                Participant.status.in_(("accepted", "registered")),
            )
        )
        or 0
    )


def lock_event_roster(
    db: Session,
    *,
    event_id: int,
    actor: User,
    reason: str | None = None,
    audit_enabled: bool = True,
) -> Event:
    if not _can_lock_roster(actor):
        raise EventServiceError("forbidden", "Недостаточно прав, чтобы зафиксировать состав", 403)
    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    if is_roster_locked(event):
        return event
    if _accepted_roster_count(db, event_id) < 1:
        raise EventServiceError(
            "roster_empty",
            "Нельзя зафиксировать пустой состав: нужен хотя бы один принятый участник",
            400,
        )
    event.roster_locked_at = datetime.now(timezone.utc)
    event.roster_locked_by_user_id = actor.id
    db.add(event)
    append_audit(
        db,
        action="event.roster.lock",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event",
        entity_id=str(event.id),
        payload={"reason": reason},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(event)
    return event


def unlock_event_roster(
    db: Session,
    *,
    event_id: int,
    actor: User,
    reason: str | None = None,
    audit_enabled: bool = True,
) -> Event:
    if not _can_lock_roster(actor):
        raise EventServiceError("forbidden", "Недостаточно прав, чтобы снять фиксацию состава", 403)
    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    if not is_roster_locked(event):
        return event
    event.roster_locked_at = None
    event.roster_locked_by_user_id = None
    db.add(event)
    append_audit(
        db,
        action="event.roster.unlock",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event",
        entity_id=str(event.id),
        payload={"reason": reason},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(event)
    return event


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

    if data.rules_profile is not None:
        from app.services.rules_profile_service import create_rules_profile

        create_rules_profile(
            db,
            event_id=event.id,
            data=data.rules_profile,
            actor=actor,
            audit_enabled=audit_enabled,
            commit=False,
        )

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


PUBLIC_EVENT_STATUSES = frozenset(
    {
        EventStatus.published.value,
        EventStatus.registration_open.value,
        EventStatus.live.value,
        EventStatus.completed.value,
    }
)


def list_events(db: Session, *, actor: User | None) -> list[Event]:
    stmt = select(Event).order_by(Event.id.desc())
    if actor is None or not can_read_all_events(actor):
        stmt = stmt.where(Event.status.in_(PUBLIC_EVENT_STATUSES))
    return list(db.scalars(stmt).all())


def get_event(
    db: Session,
    *,
    event_id: int,
    actor: User | None,
    require_mutable: bool = False,
) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise EventServiceError("not_found", "Event not found", 404)

    if actor is None or not can_read_all_events(actor):
        if event.status not in PUBLIC_EVENT_STATUSES:
            raise EventServiceError("not_found", "Event not found", 404)
    if require_mutable:
        assert_event_mutable(event)
    return event


def update_event_status(
    db: Session,
    *,
    event_id: int,
    data: EventUpdateStatus,
    actor: User,
    audit_enabled: bool = True,
) -> Event:
    """Status change is the escape hatch from archive (e.g. completed → live)."""
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
