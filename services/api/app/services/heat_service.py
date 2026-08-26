"""Heat / start list / run foundation service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.heat import Heat, Run, StartListEntry
from app.models.participant import Participant
from app.models.user import User
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, can_write_events, get_event

HEAT_STATUSES = frozenset({"planned", "ready", "on_water", "completed", "cancelled"})
ENTRY_STATUSES = frozenset(
    {"scheduled", "checked_in", "ready", "on_water", "completed", "dns", "dnf"}
)
RUN_STATUSES = frozenset({"scheduled", "ready", "on_water", "completed", "dns", "dnf"})


def list_heats(db: Session, *, event_id: int, actor: User) -> list[Heat]:
    get_event(db, event_id=event_id, actor=actor)
    return list(
        db.scalars(
            select(Heat)
            .where(Heat.event_id == event_id)
            .order_by(Heat.heat_number, Heat.id)
        ).all()
    )


def create_heat(
    db: Session,
    *,
    event_id: int,
    actor: User,
    code: str,
    title: str,
    heat_number: int = 1,
    category_id: int | None = None,
    scheduled_at: datetime | None = None,
    notes: str | None = None,
    audit_enabled: bool = True,
) -> Heat:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to manage heats", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    if category_id is not None:
        cat = db.get(Category, category_id)
        if cat is None or cat.event_id != event_id:
            raise EventServiceError("invalid_category", "Category not found for event", 400)

    heat = Heat(
        event_id=event_id,
        category_id=category_id,
        code=code.strip()[:64],
        title=title.strip()[:255],
        heat_number=heat_number,
        scheduled_at=scheduled_at,
        status="planned",
        notes=notes,
    )
    db.add(heat)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise EventServiceError("code_taken", "Heat code already exists for event", 409) from exc

    append_audit(
        db,
        action="heat.create",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="heat",
        entity_id=str(heat.id),
        payload={"event_id": event_id, "code": heat.code, "title": heat.title},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(heat)
    return heat


def update_heat_status(
    db: Session,
    *,
    event_id: int,
    heat_id: int,
    actor: User,
    status: str,
    audit_enabled: bool = True,
) -> Heat:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to manage heats", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    if status not in HEAT_STATUSES:
        raise EventServiceError("invalid_status", f"status must be one of {sorted(HEAT_STATUSES)}", 400)
    heat = db.get(Heat, heat_id)
    if heat is None or heat.event_id != event_id:
        raise EventServiceError("not_found", "Heat not found", 404)
    heat.status = status
    append_audit(
        db,
        action="heat.status",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="heat",
        entity_id=str(heat.id),
        payload={"status": status},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(heat)
    return heat


def list_start_list(db: Session, *, event_id: int, heat_id: int, actor: User) -> list[StartListEntry]:
    get_event(db, event_id=event_id, actor=actor)
    heat = db.get(Heat, heat_id)
    if heat is None or heat.event_id != event_id:
        raise EventServiceError("not_found", "Heat not found", 404)
    return list(
        db.scalars(
            select(StartListEntry)
            .where(StartListEntry.heat_id == heat_id)
            .order_by(StartListEntry.start_order, StartListEntry.id)
        ).all()
    )


def add_start_list_entry(
    db: Session,
    *,
    event_id: int,
    heat_id: int,
    actor: User,
    participant_id: int,
    start_order: int,
    bib_number: str | None = None,
    audit_enabled: bool = True,
    commit: bool = True,
) -> StartListEntry:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to manage start lists", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    heat = db.get(Heat, heat_id)
    if heat is None or heat.event_id != event_id:
        raise EventServiceError("not_found", "Heat not found", 404)

    part = db.get(Participant, participant_id)
    if part is None or part.event_id != event_id:
        raise EventServiceError("invalid_participant", "Participant not found for event", 400)
    if part.status not in ("accepted", "registered"):
        raise EventServiceError("invalid_participant", "Participant must be accepted/registered", 400)

    entry = StartListEntry(
        heat_id=heat_id,
        event_id=event_id,
        participant_id=participant_id,
        start_order=start_order,
        bib_number=bib_number,
        status="scheduled",
    )
    db.add(entry)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise EventServiceError(
            "duplicate_entry",
            "Participant or start_order already on this heat",
            409,
        ) from exc

    run = Run(
        event_id=event_id,
        heat_id=heat_id,
        start_list_entry_id=entry.id,
        participant_id=participant_id,
        attempt_no=1,
        status="scheduled",
    )
    db.add(run)

    append_audit(
        db,
        action="start_list.add",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="start_list_entry",
        entity_id=str(entry.id),
        payload={
            "heat_id": heat_id,
            "participant_id": participant_id,
            "start_order": start_order,
        },
        enabled=audit_enabled,
    )
    if commit:
        db.commit()
        db.refresh(entry)
    return entry


def fill_start_list_from_roster(
    db: Session,
    *,
    event_id: int,
    heat_id: int,
    actor: User,
    category_id: int | None = None,
    audit_enabled: bool = True,
) -> list[StartListEntry]:
    """Append accepted/registered participants not yet on this heat."""
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to manage start lists", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    heat = db.get(Heat, heat_id)
    if heat is None or heat.event_id != event_id:
        raise EventServiceError("not_found", "Heat not found", 404)

    filter_cat = category_id if category_id is not None else heat.category_id
    existing_ids = set(
        db.scalars(
            select(StartListEntry.participant_id).where(StartListEntry.heat_id == heat_id)
        ).all()
    )
    stmt = (
        select(Participant)
        .where(
            Participant.event_id == event_id,
            Participant.status.in_(("accepted", "registered")),
        )
        .order_by(Participant.full_name, Participant.id)
    )
    if filter_cat is not None:
        stmt = stmt.where(Participant.category_id == filter_cat)
    candidates = [p for p in db.scalars(stmt).all() if p.id not in existing_ids]

    max_order = db.scalar(
        select(StartListEntry.start_order)
        .where(StartListEntry.heat_id == heat_id)
        .order_by(StartListEntry.start_order.desc())
        .limit(1)
    )
    next_order = int(max_order or 0) + 1
    created: list[StartListEntry] = []
    for part in candidates:
        entry = StartListEntry(
            heat_id=heat_id,
            event_id=event_id,
            participant_id=part.id,
            start_order=next_order,
            status="scheduled",
        )
        db.add(entry)
        db.flush()
        db.add(
            Run(
                event_id=event_id,
                heat_id=heat_id,
                start_list_entry_id=entry.id,
                participant_id=part.id,
                attempt_no=1,
                status="scheduled",
            )
        )
        created.append(entry)
        next_order += 1

    append_audit(
        db,
        action="start_list.fill",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="heat",
        entity_id=str(heat_id),
        payload={"added": len(created), "category_id": filter_cat},
        enabled=audit_enabled,
    )
    db.commit()
    for entry in created:
        db.refresh(entry)
    return created


def update_start_list_status(
    db: Session,
    *,
    event_id: int,
    heat_id: int,
    entry_id: int,
    actor: User,
    status: str,
    audit_enabled: bool = True,
) -> StartListEntry:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to manage start lists", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    if status not in ENTRY_STATUSES:
        raise EventServiceError(
            "invalid_status",
            f"status must be one of {sorted(ENTRY_STATUSES)}",
            400,
        )
    entry = db.get(StartListEntry, entry_id)
    if entry is None or entry.event_id != event_id or entry.heat_id != heat_id:
        raise EventServiceError("not_found", "Start list entry not found", 404)

    now = datetime.now(timezone.utc)
    entry.status = status
    if status == "checked_in" and entry.checked_in_at is None:
        entry.checked_in_at = now
    elif status == "ready" and entry.ready_at is None:
        entry.ready_at = now
    elif status == "on_water" and entry.on_water_at is None:
        entry.on_water_at = now
    elif status == "completed" and entry.completed_at is None:
        entry.completed_at = now

    run = db.scalar(
        select(Run)
        .where(Run.start_list_entry_id == entry.id, Run.attempt_no == 1)
        .limit(1)
    )
    if run is not None and status in RUN_STATUSES:
        run.status = status
        if status == "on_water" and run.started_at is None:
            run.started_at = now
        if status in ("completed", "dns", "dnf") and run.finished_at is None:
            run.finished_at = now

    append_audit(
        db,
        action="start_list.status",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="start_list_entry",
        entity_id=str(entry.id),
        payload={"status": status},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(entry)
    return entry


def list_runs_for_heat(db: Session, *, event_id: int, heat_id: int, actor: User) -> list[Run]:
    get_event(db, event_id=event_id, actor=actor)
    heat = db.get(Heat, heat_id)
    if heat is None or heat.event_id != event_id:
        raise EventServiceError("not_found", "Heat not found", 404)
    return list(
        db.scalars(select(Run).where(Run.heat_id == heat_id).order_by(Run.id)).all()
    )
