"""Document upload / delete for event files under data/documents."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.event import Event
from app.models.user import User
from app.services.audit_service import append_audit
from app.services.competition_service import get_document
from app.services.event_service import EventServiceError, can_write_events, get_event

ALLOWED_EXTENSIONS = frozenset({".pdf", ".xlsx", ".xls"})
ALLOWED_KINDS = frozenset(
    {"bulletin", "protocol", "schedule", "rules", "start_list", "other"}
)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


def _safe_filename(name: str) -> str:
    base = Path(name or "file").name
    cleaned = re.sub(r"[^\w.\-()+ ]+", "_", base, flags=re.UNICODE).strip(" ._")
    if not cleaned:
        cleaned = "file"
    return cleaned[:180]


def _documents_base(repo_root: Path) -> Path:
    return (repo_root / "data" / "documents").resolve()


def upload_document(
    db: Session,
    *,
    event_id: int,
    actor: User,
    file: UploadFile,
    title: str,
    kind: str = "other",
    language: str | None = None,
    description: str | None = None,
    repo_root: Path,
    audit_enabled: bool = True,
) -> Document:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to upload documents", 403)

    event = get_event(db, event_id=event_id, actor=actor)
    kind_norm = (kind or "other").strip().lower()
    if kind_norm not in ALLOWED_KINDS:
        raise EventServiceError(
            "invalid_kind",
            f"kind must be one of: {', '.join(sorted(ALLOWED_KINDS))}",
            400,
        )

    original = file.filename or "upload.bin"
    safe_name = _safe_filename(original)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise EventServiceError(
            "invalid_file_type",
            "Allowed types: .pdf, .xlsx, .xls",
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

    base = _documents_base(repo_root)
    event_dir = base / event.slug
    event_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    dest = (event_dir / stored_name).resolve()
    if not str(dest).startswith(str(base)):
        raise EventServiceError("invalid_path", "Invalid document path", 400)
    dest.write_bytes(raw)

    title_clean = (title or "").strip() or Path(safe_name).stem
    doc = Document(
        event_id=event.id,
        title=title_clean[:255],
        kind=kind_norm,
        language=(language or None),
        file_name=safe_name,
        relative_path=f"{event.slug}/{stored_name}",
        description=(description or None),
    )
    db.add(doc)
    db.flush()

    append_audit(
        db,
        action="document.upload",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="document",
        entity_id=str(doc.id),
        payload={
            "event_id": event.id,
            "title": doc.title,
            "kind": doc.kind,
            "file_name": doc.file_name,
            "bytes": len(raw),
        },
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(
    db: Session,
    *,
    event_id: int,
    document_id: int,
    actor: User,
    repo_root: Path,
    audit_enabled: bool = True,
) -> None:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to delete documents", 403)

    doc = get_document(db, event_id=event_id, document_id=document_id, actor=actor)
    base = _documents_base(repo_root)
    path = (base / doc.relative_path).resolve()
    if str(path).startswith(str(base)) and path.is_file():
        path.unlink(missing_ok=True)

    append_audit(
        db,
        action="document.delete",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="document",
        entity_id=str(doc.id),
        payload={"event_id": event_id, "title": doc.title, "file_name": doc.file_name},
        enabled=audit_enabled,
    )
    db.delete(doc)
    db.commit()
