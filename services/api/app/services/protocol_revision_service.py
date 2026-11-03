"""Approve/list official protocol revisions (ADR-0017)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.protocol_revision import OfficialProtocolRevision
from app.models.user import User
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, can_write_events, get_event
from app.services.official_protocol_service import build_official_protocol_bundle


def list_revisions(db: Session, *, event_id: int, actor: User) -> list[OfficialProtocolRevision]:
    get_event(db, event_id=event_id, actor=actor)
    return list(
        db.scalars(
            select(OfficialProtocolRevision)
            .where(OfficialProtocolRevision.event_id == event_id)
            .order_by(OfficialProtocolRevision.revision_no.desc())
        ).all()
    )


def get_revision(
    db: Session,
    *,
    event_id: int,
    revision_id: int,
    actor: User,
) -> OfficialProtocolRevision:
    get_event(db, event_id=event_id, actor=actor)
    row = db.scalar(
        select(OfficialProtocolRevision).where(
            OfficialProtocolRevision.id == revision_id,
            OfficialProtocolRevision.event_id == event_id,
        )
    )
    if row is None:
        raise EventServiceError("not_found", "Protocol revision not found", 404)
    return row


def approve_revision(
    db: Session,
    *,
    event_id: int,
    actor: User,
    note: str | None = None,
    audit_enabled: bool = True,
) -> OfficialProtocolRevision:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Недостаточно прав для утверждения протокола", 403)

    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    bundle = build_official_protocol_bundle(db, event_id=event_id, actor=actor)
    if not bundle.readiness.official_ready:
        raise EventServiceError(
            "not_ready",
            "Протокол не готов к утверждению: " + ", ".join(bundle.readiness.blockers),
            400,
        )

    payload = bundle.model_dump(mode="json")
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    next_no = int(
        db.scalar(
            select(func.coalesce(func.max(OfficialProtocolRevision.revision_no), 0)).where(
                OfficialProtocolRevision.event_id == event_id
            )
        )
        or 0
    ) + 1

    row = OfficialProtocolRevision(
        event_id=event_id,
        revision_no=next_no,
        status="approved",
        note=(note or "").strip() or None,
        snapshot_json=raw,
        content_sha256=digest,
        created_by_user_id=actor.id,
    )
    db.add(row)
    db.flush()
    append_audit(
        db,
        action="protocol.revision_approve",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="official_protocol_revision",
        entity_id=str(row.id),
        payload={"revision_no": next_no, "sha256": digest},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(row)
    return row


def revision_to_dict(row: OfficialProtocolRevision) -> dict[str, Any]:
    return {
        "id": row.id,
        "event_id": row.event_id,
        "revision_no": row.revision_no,
        "status": row.status,
        "note": row.note,
        "content_sha256": row.content_sha256,
        "created_by_user_id": row.created_by_user_id,
        "created_at": row.created_at,
    }
