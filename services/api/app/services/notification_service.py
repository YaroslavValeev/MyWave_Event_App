"""In-app notifications: persist status events that must be visible without SMTP."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.roles import EVENT_WRITE_ROLES
from app.models.notification import Notification
from app.models.user import User


def create_notification(
    db: Session,
    *,
    user_id: int,
    kind: str,
    title: str,
    body: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> Notification:
    row = Notification(
        user_id=user_id,
        kind=kind,
        title=title,
        body=body,
        entity_type=entity_type,
        entity_id=entity_id,
        is_read=False,
    )
    db.add(row)
    db.flush()
    return row


def notify_event_staff(
    db: Session,
    *,
    kind: str,
    title: str,
    body: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    exclude_user_id: int | None = None,
) -> None:
    role_values = [role.value for role in EVENT_WRITE_ROLES]
    users = list(db.scalars(select(User).where(User.role.in_(role_values), User.status == "active")))
    seen: set[int] = set()
    for user in users:
        if exclude_user_id is not None and user.id == exclude_user_id:
            continue
        if user.id in seen:
            continue
        seen.add(user.id)
        create_notification(
            db,
            user_id=user.id,
            kind=kind,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
        )


def list_notifications(db: Session, *, user_id: int, limit: int = 50) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def unread_count(db: Session, *, user_id: int) -> int:
    value = db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    )
    return int(value or 0)


def mark_read(db: Session, *, user_id: int, notification_id: int) -> Notification | None:
    row = db.get(Notification, notification_id)
    if row is None or row.user_id != user_id:
        return None
    if not row.is_read:
        row.is_read = True
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def mark_all_read(db: Session, *, user_id: int) -> int:
    rows = list(
        db.scalars(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
    )
    for row in rows:
        row.is_read = True
        db.add(row)
    db.commit()
    return len(rows)
