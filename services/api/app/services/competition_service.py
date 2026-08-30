"""Read helpers for categories / participants / documents."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.document import Document
from app.models.event import Event
from app.models.official import Official
from app.models.participant import Participant
from app.models.training_slot import TrainingSlot
from app.models.user import User
from app.services.event_service import EventServiceError, get_event


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


def list_documents(db: Session, *, event_id: int, actor: User) -> list[Document]:
    get_event(db, event_id=event_id, actor=actor)
    return list(
        db.scalars(
            select(Document).where(Document.event_id == event_id).order_by(Document.title)
        ).all()
    )


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
