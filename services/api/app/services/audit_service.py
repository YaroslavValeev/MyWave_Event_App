"""Audit log service (append-only stub)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def append_audit(
    db: Session,
    *,
    action: str,
    actor_user_id: int | None = None,
    actor_email: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict[str, Any] | None = None,
    enabled: bool = True,
) -> AuditEvent | None:
    if not enabled:
        return None
    event = AuditEvent(
        action=action,
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type=entity_type,
        entity_id=entity_id,
        payload_json=json.dumps(payload, default=str) if payload is not None else None,
    )
    db.add(event)
    db.flush()
    return event


def list_audit_events(db: Session, *, limit: int = 100, offset: int = 0) -> list[AuditEvent]:
    stmt = (
        select(AuditEvent)
        .order_by(AuditEvent.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())
