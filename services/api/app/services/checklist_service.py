"""Event checklist service — preparation SoT inside Event App."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.checklist import EventChecklistItem
from app.models.document import Document
from app.models.event import Event
from app.models.heat import Heat, StartListEntry
from app.models.official import Official
from app.models.participant import Participant
from app.models.user import User
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, can_write_events, get_event

DEFAULT_CHECKLIST: tuple[tuple[str, str, int], ...] = (
    ("documents", "Документы события загружены", 10),
    ("categories", "Категории настроены", 20),
    ("officials", "Судейская коллегия назначена", 30),
    ("registration", "Регистрация открыта / проверена", 40),
    ("roster", "Состав (roster) проверен", 50),
    ("medical", "Медфлаги / справки просмотрены", 60),
    ("start_lists", "Стартовые протоколы / heats готовы", 70),
)


def ensure_checklist(db: Session, *, event_id: int, actor: User) -> list[EventChecklistItem]:
    get_event(db, event_id=event_id, actor=actor)
    existing = {
        item.code: item
        for item in db.scalars(
            select(EventChecklistItem).where(EventChecklistItem.event_id == event_id)
        ).all()
    }
    created = False
    for code, title, sort_order in DEFAULT_CHECKLIST:
        if code in existing:
            continue
        db.add(
            EventChecklistItem(
                event_id=event_id,
                code=code,
                title=title,
                sort_order=sort_order,
                is_done=False,
            )
        )
        created = True
    if created:
        db.commit()

    items = _ordered(db, event_id)
    _auto_sync(db, event_id=event_id, items=items)
    return _ordered(db, event_id)


def _ordered(db: Session, event_id: int) -> list[EventChecklistItem]:
    return list(
        db.scalars(
            select(EventChecklistItem)
            .where(EventChecklistItem.event_id == event_id)
            .order_by(EventChecklistItem.sort_order, EventChecklistItem.id)
        ).all()
    )


def _auto_sync(db: Session, *, event_id: int, items: list[EventChecklistItem]) -> None:
    """Mark obvious prep items done from existing data (never unchecks manual)."""
    by_code = {i.code: i for i in items}
    docs = db.scalar(select(func.count()).select_from(Document).where(Document.event_id == event_id)) or 0
    cats = db.scalar(select(func.count()).select_from(Category).where(Category.event_id == event_id)) or 0
    offs = db.scalar(select(func.count()).select_from(Official).where(Official.event_id == event_id)) or 0
    roster = (
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
    heats = db.scalar(select(func.count()).select_from(Heat).where(Heat.event_id == event_id)) or 0
    entries = (
        db.scalar(
            select(func.count()).select_from(StartListEntry).where(StartListEntry.event_id == event_id)
        )
        or 0
    )
    ev = db.get(Event, event_id)
    hints = {
        "documents": docs > 0,
        "categories": cats > 0,
        "officials": offs > 0,
        "roster": roster > 0,
        "registration": bool(ev and ev.status in ("registration_open", "live", "completed")),
        "start_lists": heats > 0 and entries > 0,
    }
    changed = False
    now = datetime.now(timezone.utc)
    for code, should in hints.items():
        item = by_code.get(code)
        if item is None or item.is_done or not should:
            continue
        item.is_done = True
        item.done_at = now
        item.done_by_user_id = None
        changed = True
    if changed:
        db.commit()


def set_checklist_item(
    db: Session,
    *,
    event_id: int,
    item_id: int,
    actor: User,
    is_done: bool,
    audit_enabled: bool = True,
) -> EventChecklistItem:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to update checklist", 403)
    get_event(db, event_id=event_id, actor=actor)
    item = db.get(EventChecklistItem, item_id)
    if item is None or item.event_id != event_id:
        raise EventServiceError("not_found", "Checklist item not found", 404)

    item.is_done = is_done
    if is_done:
        item.done_at = datetime.now(timezone.utc)
        item.done_by_user_id = actor.id
    else:
        item.done_at = None
        item.done_by_user_id = None

    append_audit(
        db,
        action="checklist.update",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event_checklist_item",
        entity_id=str(item.id),
        payload={"event_id": event_id, "code": item.code, "is_done": is_done},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(item)
    return item
