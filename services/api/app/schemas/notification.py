"""Notification API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    kind: str
    title: str
    body: str
    entity_type: str | None
    entity_id: str | None
    is_read: bool
    created_at: str


class NotificationListResponse(BaseModel):
    items: list[NotificationOut]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int
