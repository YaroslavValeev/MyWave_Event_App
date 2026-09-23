"""Protocol capture upload, verify, publish."""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.models.protocol_capture import ProtocolCapture
from app.models.user import User
from app.schemas.protocol import ProtocolCaptureUpdate
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, assert_event_mutable, get_event

ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".pdf"})
ALLOWED_KINDS = frozenset({"judge_sheet", "chief_protocol", "photo_result", "other"})
ALLOWED_STATUSES = frozenset({"draft", "verified", "published", "rejected"})
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB

PROTOCOL_UPLOAD_ROLES = EVENT_WRITE_ROLES | frozenset({Role.judge, Role.chief_judge})
PROTOCOL_VERIFY_ROLES = EVENT_WRITE_ROLES | frozenset({Role.chief_judge})
PROTOCOL_PUBLISH_ROLES = frozenset({Role.chief_judge, Role.platform_admin})


def _role_of(user: User) -> Role:
    return Role(user.role)


def can_upload_protocol(user: User) -> bool:
    return _role_of(user) in PROTOCOL_UPLOAD_ROLES


def can_verify_protocol(user: User) -> bool:
    return _role_of(user) in PROTOCOL_VERIFY_ROLES


def can_publish_protocol(user: User) -> bool:
    return _role_of(user) in PROTOCOL_PUBLISH_ROLES


def _safe_filename(name: str) -> str:
    base = Path(name or "file").name
    cleaned = re.sub(r"[^\w.\-()+ ]+", "_", base, flags=re.UNICODE).strip(" ._")
    if not cleaned:
        cleaned = "file"
    return cleaned[:180]


def _protocols_base(repo_root: Path) -> Path:
    return (repo_root / "data" / "protocols").resolve()


def list_protocol_captures(
    db: Session,
    *,
    event_id: int,
    actor: User,
    heat_id: int | None = None,
) -> list[ProtocolCapture]:
    get_event(db, event_id=event_id, actor=actor)
    stmt = select(ProtocolCapture).where(ProtocolCapture.event_id == event_id)
    if heat_id is not None:
        stmt = stmt.where(ProtocolCapture.heat_id == heat_id)
    stmt = stmt.order_by(ProtocolCapture.id.desc())
    return list(db.scalars(stmt).all())


def get_protocol_capture(
    db: Session,
    *,
    event_id: int,
    capture_id: int,
    actor: User,
) -> ProtocolCapture:
    get_event(db, event_id=event_id, actor=actor)
    capture = db.scalar(
        select(ProtocolCapture).where(
            ProtocolCapture.id == capture_id,
            ProtocolCapture.event_id == event_id,
        )
    )
    if capture is None:
        raise EventServiceError("not_found", "Protocol capture not found", 404)
    return capture


def upload_protocol_capture(
    db: Session,
    *,
    event_id: int,
    actor: User,
    file: UploadFile,
    title: str,
    kind: str = "judge_sheet",
    heat_id: int | None = None,
    notes: str | None = None,
    repo_root: Path,
    audit_enabled: bool = True,
) -> ProtocolCapture:
    if not can_upload_protocol(actor):
        raise EventServiceError("forbidden", "Insufficient role to upload protocol capture", 403)

    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    kind_norm = (kind or "judge_sheet").strip().lower()
    if kind_norm not in ALLOWED_KINDS:
        raise EventServiceError(
            "invalid_kind",
            f"kind must be one of: {', '.join(sorted(ALLOWED_KINDS))}",
            400,
        )

    if heat_id is not None:
        from app.models.heat import Heat

        heat = db.get(Heat, heat_id)
        if heat is None or heat.event_id != event.id:
            raise EventServiceError("invalid_heat", "Heat not found for this event", 400)

    original = file.filename or "upload.bin"
    safe_name = _safe_filename(original)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise EventServiceError(
            "invalid_file_type",
            "Allowed types: .jpg, .jpeg, .png, .webp, .pdf",
            400,
        )

    raw = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) == 0:
        raise EventServiceError("empty_file", "Uploaded file is empty", 400)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise EventServiceError(
            "file_too_large",
            f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit",
            400,
        )

    base = _protocols_base(repo_root)
    event_dir = base / event.slug
    event_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    dest = (event_dir / stored_name).resolve()
    if not str(dest).startswith(str(base)):
        raise EventServiceError("invalid_path", "Invalid protocol path", 400)
    dest.write_bytes(raw)

    mime = file.content_type or "application/octet-stream"
    if suffix == ".pdf":
        mime = "application/pdf"
    elif suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".png":
        mime = "image/png"
    elif suffix == ".webp":
        mime = "image/webp"

    title_clean = (title or "").strip() or Path(safe_name).stem
    capture = ProtocolCapture(
        event_id=event.id,
        heat_id=heat_id,
        title=title_clean[:255],
        kind=kind_norm,
        file_name=safe_name,
        relative_path=f"{event.slug}/{stored_name}",
        mime_type=mime,
        notes=(notes or None),
        created_by_user_id=actor.id,
        status="draft",
    )
    db.add(capture)
    db.flush()

    append_audit(
        db,
        action="protocol.upload",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="protocol_capture",
        entity_id=str(capture.id),
        payload={
            "event_id": event.id,
            "heat_id": heat_id,
            "title": capture.title,
            "kind": capture.kind,
            "file_name": capture.file_name,
            "bytes": len(raw),
        },
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(capture)
    return capture


def update_protocol_capture(
    db: Session,
    *,
    event_id: int,
    capture_id: int,
    actor: User,
    data: ProtocolCaptureUpdate,
    audit_enabled: bool = True,
) -> ProtocolCapture:
    capture = get_protocol_capture(db, event_id=event_id, capture_id=capture_id, actor=actor)
    event = get_event(db, event_id=event_id, actor=actor)
    assert_event_mutable(event)

    if data.title is not None:
        if not can_upload_protocol(actor):
            raise EventServiceError("forbidden", "Insufficient role to edit protocol capture", 403)
        capture.title = data.title.strip()[:255]

    if data.notes is not None:
        if not can_upload_protocol(actor):
            raise EventServiceError("forbidden", "Insufficient role to edit protocol capture", 403)
        capture.notes = data.notes

    if data.extracted is not None:
        if not can_verify_protocol(actor):
            raise EventServiceError("forbidden", "Insufficient role to set extracted data", 403)
        capture.extracted_json = json.dumps(data.extracted, ensure_ascii=False)

    if data.status is not None:
        status = data.status
        if status not in ALLOWED_STATUSES:
            raise EventServiceError("invalid_status", f"status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}", 400)

        if status == "published":
            if not can_publish_protocol(actor):
                raise EventServiceError(
                    "chief_approval_required",
                    "Официальный протокол публикует главный судья (или platform_admin)",
                    403,
                )
            capture.verified_by_user_id = actor.id
            capture.verified_at = datetime.now(UTC)
        elif status in {"verified", "rejected"}:
            if not can_verify_protocol(actor):
                raise EventServiceError("forbidden", "Insufficient role to verify protocol capture", 403)
            capture.verified_by_user_id = actor.id
            capture.verified_at = datetime.now(UTC)
        elif status == "draft" and not can_verify_protocol(actor):
            raise EventServiceError("forbidden", "Insufficient role to reset protocol status", 403)

        capture.status = status

    db.flush()
    append_audit(
        db,
        action="protocol.update",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="protocol_capture",
        entity_id=str(capture.id),
        payload={"event_id": event_id, "status": capture.status, "title": capture.title},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(capture)
    return capture


def protocol_capture_count(db: Session, event_id: int) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(ProtocolCapture).where(ProtocolCapture.event_id == event_id)
        )
        or 0
    )
