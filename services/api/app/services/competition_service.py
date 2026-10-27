"""Read helpers for categories / participants / documents."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.models.category import Category
from app.models.document import Document
from app.models.event import Event
from app.models.official import Official
from app.models.participant import Participant
from app.models.training_slot import TrainingSlot
from app.models.user import User
from app.services.event_service import EventServiceError, get_event

RESTRICTED_DOCUMENT_CLASSES = frozenset(
    {"medical-restricted", "consent-restricted", "admin-only", "media-rights"}
)


def list_documents(db: Session, *, event_id: int, actor: User) -> list[Document]:
    get_event(db, event_id=event_id, actor=actor)
    items = list(
        db.scalars(
            select(Document).where(Document.event_id == event_id).order_by(Document.title)
        ).all()
    )
    if Role(actor.role) in EVENT_WRITE_ROLES:
        return items
    return [doc for doc in items if doc.access_class not in RESTRICTED_DOCUMENT_CLASSES]


def list_categories(db: Session, *, event_id: int, actor: User | None) -> list[Category]:
    get_event(db, event_id=event_id, actor=actor)
    return list(
        db.scalars(
            select(Category).where(Category.event_id == event_id).order_by(Category.title)
        ).all()
    )


def list_participants(
    db: Session,
    *,
    event_id: int,
    actor: User,
    category_id: int | None = None,
) -> list[Participant]:
    get_event(db, event_id=event_id, actor=actor)
    stmt = (
        select(Participant)
        .where(
            Participant.event_id == event_id,
            Participant.status.in_(("accepted", "registered")),
        )
        .order_by(Participant.full_name)
    )
    if category_id is not None:
        stmt = stmt.where(Participant.category_id == category_id)
    return list(db.scalars(stmt).all())


def list_officials(db: Session, *, event_id: int, actor: User | None) -> list[Official]:
    get_event(db, event_id=event_id, actor=actor)
    return list(
        db.scalars(
            select(Official)
            .where(Official.event_id == event_id)
            .order_by(Official.sort_order, Official.id)
        ).all()
    )


def list_training_slots(
    db: Session,
    *,
    event_id: int,
    actor: User,
    discipline: str | None = None,
    only_booked: bool = False,
) -> list[TrainingSlot]:
    get_event(db, event_id=event_id, actor=actor)
    stmt = (
        select(TrainingSlot)
        .where(TrainingSlot.event_id == event_id)
        .order_by(TrainingSlot.slot_date, TrainingSlot.sort_order, TrainingSlot.id)
    )
    if discipline:
        stmt = stmt.where(TrainingSlot.discipline == discipline)
    if only_booked:
        stmt = stmt.where(TrainingSlot.status == "booked")
    return list(db.scalars(stmt).all())


def get_document(db: Session, *, event_id: int, document_id: int, actor: User) -> Document:
    get_event(db, event_id=event_id, actor=actor)
    doc = db.get(Document, document_id)
    if doc is None or doc.event_id != event_id:
        raise EventServiceError("not_found", "Document not found", 404)
    if doc.access_class in RESTRICTED_DOCUMENT_CLASSES and Role(actor.role) not in EVENT_WRITE_ROLES:
        raise EventServiceError("forbidden", "Недостаточно прав для этого документа", 403)
    return doc


def event_counts(db: Session, event: Event) -> tuple[int, int, int, int, int]:
    cats = db.scalar(select(func.count()).select_from(Category).where(Category.event_id == event.id)) or 0
    parts = (
        db.scalar(
            select(func.count())
            .select_from(Participant)
            .where(
                Participant.event_id == event.id,
                Participant.status.in_(("accepted", "registered")),
            )
        )
        or 0
    )
    docs = db.scalar(select(func.count()).select_from(Document).where(Document.event_id == event.id)) or 0
    offs = db.scalar(select(func.count()).select_from(Official).where(Official.event_id == event.id)) or 0
    slots = (
        db.scalar(select(func.count()).select_from(TrainingSlot).where(TrainingSlot.event_id == event.id))
        or 0
    )
    return int(cats), int(parts), int(docs), int(offs), int(slots)


KAZAN_2026_PROGRAM = (
    "11.08 — запасной тренировочный день",
    "12.08 — основные тренировочные слоты",
    "13.08 — квалификация · 14.08 полуфиналы · 15.08 финалы · 16.08 резерв",
    "Акватория: оз. Нижний Кабан; тренировки Wakesurf/Wakeskim — ул. Торфяная, 83",
)


def _is_kazan_2026(event: Event) -> bool:
    """Bulletin program is bound to the Kazan championship event, not to every card."""
    slug = (event.slug or "").casefold()
    title = (event.title or "").casefold()
    if slug == "chr-pr-kazan-2026" or "chr-pr-kazan" in slug:
        return True
    has_kazan = "казан" in title or "kazan" in title
    has_champ = any(token in title for token in ("чемпионат", "первенство"))
    return has_kazan and has_champ


def _fmt_day(value: datetime | date | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%d.%m.%Y")


def build_schedule_hint(db: Session, event: Event) -> tuple[str, list[str]]:
    """Schedule text must come from this event — never a global Kazan stub."""
    cats, parts, docs, offs, slot_count = event_counts(db, event)
    start = _fmt_day(event.starts_at)
    end = _fmt_day(event.ends_at)
    if start and end and start != end:
        period = f"{start} — {end}"
    else:
        period = start or end or "даты не заданы"

    place = ", ".join(p for p in (event.city, event.venue or event.location) if p) or "место не задано"
    discs = (event.disciplines or "").strip() or "дисциплины не заданы"
    summary = f"{event.title}: {period}, {place}. {discs}."

    notes: list[str] = [
        f"В этом событии: состав {parts}, категорий {cats}, судей {offs}, документов {docs}.",
    ]
    slot_rows = list(
        db.scalars(
            select(TrainingSlot)
            .where(TrainingSlot.event_id == event.id)
            .order_by(TrainingSlot.slot_date, TrainingSlot.sort_order)
        ).all()
    )
    if slot_rows:
        days = sorted({_fmt_day(s.slot_date) for s in slot_rows if s.slot_date})
        venues = sorted({s.venue for s in slot_rows if s.venue})
        notes.append(
            f"Тренировочные слоты этого события: {len(slot_rows)}"
            + (f" ({', '.join(d for d in days if d)})" if days else "")
            + (f"; площадки: {', '.join(venues)}" if venues else "")
            + "."
        )
    else:
        notes.append("Тренировочные слоты для этого события ещё не загружены.")

    if _is_kazan_2026(event):
        notes.append("Программа из бюллетеня ЧР/ПР Казань 2026 (только для этого события):")
        notes.extend(KAZAN_2026_PROGRAM)
    elif slot_count == 0:
        notes.append("Расписание других событий сюда не подставляется.")

    return summary, notes

