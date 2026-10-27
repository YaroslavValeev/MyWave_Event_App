"""Event applications (self-serve Participant rows)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.models.category import Category
from app.models.event import EventStatus
from app.models.participant import Participant
from app.models.user import User
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, assert_roster_unlocked, get_event
from app.services.notification_service import create_notification, notify_event_staff

PUBLIC_ROSTER_STATUSES = frozenset({"accepted", "registered"})
BLOCKING_STATUSES = frozenset({"pending", "accepted", "registered"})


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _require_organizer(actor: User) -> None:
    if Role(actor.role) not in EVENT_WRITE_ROLES:
        raise ApplicationError("forbidden", "Недостаточно прав", 403)


def create_application(
    db: Session,
    *,
    event_id: int,
    actor: User,
    category_id: int | None,
    club: str | None,
    region: str | None,
    city: str | None,
    gender: str | None,
    birth_year: int | None,
    audit_enabled: bool,
) -> Participant:
    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    try:
        assert_roster_unlocked(event)
    except EventServiceError as exc:
        raise ApplicationError(exc.code, exc.message, exc.status_code) from exc
    if event.status != EventStatus.registration_open.value:
        raise ApplicationError(
            "registration_closed",
            "Регистрация на событие закрыта",
            409,
        )
    if not actor.display_name or len(actor.display_name.strip()) < 2:
        raise ApplicationError(
            "display_name_required",
            "В профиле нужно указать ФИО (display_name)",
            400,
        )

    existing = db.scalar(
        select(Participant).where(
            Participant.event_id == event_id,
            Participant.user_id == actor.id,
        )
    )
    if existing is not None and existing.status in BLOCKING_STATUSES:
        raise ApplicationError(
            "already_applied",
            "Заявка уже подана или вы уже в списке участников",
            409,
        )

    if category_id is not None:
        cat = db.get(Category, category_id)
        if cat is None or cat.event_id != event_id:
            raise ApplicationError("invalid_category", "Категория не найдена", 400)

    if existing is not None and existing.status == "rejected":
        existing.status = "pending"
        existing.category_id = category_id
        existing.club = club
        existing.region = region
        existing.city = city
        existing.gender = gender
        existing.birth_year = birth_year
        existing.full_name = actor.display_name.strip()
        existing.phone = actor.phone
        part = existing
    else:
        part = Participant(
            event_id=event_id,
            category_id=category_id,
            user_id=actor.id,
            full_name=actor.display_name.strip(),
            club=club,
            region=region,
            city=city,
            gender=gender,
            birth_year=birth_year,
            phone=actor.phone,
            status="pending",
        )
        db.add(part)

    db.flush()
    append_audit(
        db,
        action="application.create",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="participant",
        entity_id=str(part.id),
        payload={"event_id": event_id, "status": part.status},
        enabled=audit_enabled,
    )
    create_notification(
        db,
        user_id=actor.id,
        kind="application.submitted",
        title="Заявка отправлена",
        body=f"Заявка на «{event.title}» принята в очередь организатора.",
        entity_type="participant",
        entity_id=str(part.id),
    )
    notify_event_staff(
        db,
        kind="application.submitted_staff",
        title="Новая заявка на участие",
        body=f"{part.full_name} подал заявку на «{event.title}».",
        entity_type="participant",
        entity_id=str(part.id),
        exclude_user_id=actor.id,
    )
    db.commit()
    db.refresh(part)
    return part


def get_my_application(db: Session, *, event_id: int, actor: User) -> Participant | None:
    get_event(db, event_id=event_id, actor=actor)
    return db.scalar(
        select(Participant).where(
            Participant.event_id == event_id,
            Participant.user_id == actor.id,
        )
    )


def list_applications(
    db: Session,
    *,
    event_id: int,
    actor: User,
    status: str | None = "pending",
) -> list[Participant]:
    get_event(db, event_id=event_id, actor=actor)
    _require_organizer(actor)
    stmt = select(Participant).where(Participant.event_id == event_id).order_by(Participant.id.desc())
    if status:
        stmt = stmt.where(Participant.status == status)
    else:
        stmt = stmt.where(Participant.user_id.is_not(None))
    return list(db.scalars(stmt).all())


def decide_application(
    db: Session,
    *,
    event_id: int,
    participant_id: int,
    actor: User,
    status: str,
    audit_enabled: bool,
) -> Participant:
    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    _require_organizer(actor)
    part = db.get(Participant, participant_id)
    if part is None or part.event_id != event_id:
        raise ApplicationError("not_found", "Заявка не найдена", 404)
    if part.status != "pending":
        raise ApplicationError("not_pending", "Заявка уже обработана", 409)
    if status not in {"accepted", "rejected"}:
        raise ApplicationError("invalid_status", "status must be accepted|rejected", 400)
    if status == "accepted":
        try:
            assert_roster_unlocked(event)
        except EventServiceError as exc:
            raise ApplicationError(exc.code, exc.message, exc.status_code) from exc

    part.status = status
    db.add(part)
    append_audit(
        db,
        action=f"application.{status}",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="participant",
        entity_id=str(part.id),
        payload={"event_id": event_id, "status": status},
        enabled=audit_enabled,
    )
    if part.user_id is not None:
        decided_label = "принята" if status == "accepted" else "отклонена"
        create_notification(
            db,
            user_id=part.user_id,
            kind=f"application.{status}",
            title="Решение по заявке",
            body=f"Заявка на участие {decided_label}.",
            entity_type="participant",
            entity_id=str(part.id),
        )
    db.commit()
    db.refresh(part)
    return part
