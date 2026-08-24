"""Current-user in-app notification log."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.errors import raise_api_error
from app.schemas.notification import (
    NotificationListResponse,
    NotificationOut,
    UnreadCountResponse,
)
from app.services.notification_service import (
    list_notifications,
    mark_all_read,
    mark_read,
    unread_count,
)

router = APIRouter(tags=["notifications"])


def _out(row) -> NotificationOut:
    return NotificationOut(
        id=row.id,
        kind=row.kind,
        title=row.title,
        body=row.body,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        is_read=row.is_read,
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


@router.get("/me/notifications", response_model=NotificationListResponse)
def get_my_notifications(db: DbSession, user: CurrentUser) -> NotificationListResponse:
    items = list_notifications(db, user_id=user.id)
    return NotificationListResponse(
        items=[_out(row) for row in items],
        total=len(items),
        unread_count=unread_count(db, user_id=user.id),
    )


@router.get("/me/notifications/unread-count", response_model=UnreadCountResponse)
def get_unread_count(db: DbSession, user: CurrentUser) -> UnreadCountResponse:
    return UnreadCountResponse(unread_count=unread_count(db, user_id=user.id))


@router.post("/me/notifications/read-all", response_model=UnreadCountResponse)
def post_read_all(db: DbSession, user: CurrentUser) -> UnreadCountResponse:
    mark_all_read(db, user_id=user.id)
    return UnreadCountResponse(unread_count=0)


@router.post("/me/notifications/{notification_id}/read", response_model=NotificationOut)
def post_mark_read(
    notification_id: int, db: DbSession, user: CurrentUser
) -> NotificationOut:
    row = mark_read(db, user_id=user.id, notification_id=notification_id)
    if row is None:
        raise_api_error(404, "notification_not_found", "Уведомление не найдено")
    return _out(row)
