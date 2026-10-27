"""Field moments: emotional / operational camera captures, not official protocol."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.models.field_moment import FieldMoment
from app.models.user import User
from app.schemas.field_moment import FieldMomentUpdate
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, assert_event_mutable, get_event

ALLOWED_PHOTO = frozenset({".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"})
ALLOWED_VIDEO = frozenset({".mp4", ".webm", ".mov", ".m4v"})
ALLOWED_EXTENSIONS = ALLOWED_PHOTO | ALLOWED_VIDEO
ALLOWED_POV = frozenset(
    {"backstage", "boat_pilot", "start_marshal", "on_water", "crowd", "other"}
)
ALLOWED_STATUSES = frozenset({"draft", "approved", "withheld"})
MAX_PHOTO_BYTES = 15 * 1024 * 1024
MAX_VIDEO_BYTES = 40 * 1024 * 1024

POV_TITLES_RU = {
    "backstage": "Бэкстейдж",
    "boat_pilot": "Глазами пилота",
    "start_marshal": "Маршал на старте",
    "on_water": "На воде",
    "crowd": "Зрители и эмоции",
    "other": "Момент события",
}

FIELD_CAPTURE_ROLES = EVENT_WRITE_ROLES | frozenset(
    {Role.media, Role.commentator, Role.support, Role.chief_judge}
)
FIELD_MODERATE_ROLES = EVENT_WRITE_ROLES | frozenset({Role.chief_judge})


def _role_of(user: User) -> Role:
    return Role(user.role)


def can_capture_field_moments(user: User) -> bool:
    return _role_of(user) in FIELD_CAPTURE_ROLES


def can_moderate_field_moments(user: User) -> bool:
    return _role_of(user) in FIELD_MODERATE_ROLES


def _safe_filename(name: str) -> str:
    base = Path(name or "file").name
    cleaned = re.sub(r"[^\w.\-()+ ]+", "_", base, flags=re.UNICODE).strip(" ._")
    if not cleaned:
        cleaned = "file"
    return cleaned[:180]


def _media_base(repo_root: Path) -> Path:
    return (repo_root / "data" / "field-media").resolve()


def list_field_moments(
    db: Session,
    *,
    event_id: int,
    actor: User,
    heat_id: int | None = None,
) -> list[FieldMoment]:
    if not can_capture_field_moments(actor):
        raise EventServiceError("forbidden", "Эта роль не может смотреть полевые моменты", 403)
    get_event(db, event_id=event_id, actor=actor)
    stmt = select(FieldMoment).where(FieldMoment.event_id == event_id)
    if heat_id is not None:
        stmt = stmt.where(FieldMoment.heat_id == heat_id)
    stmt = stmt.order_by(FieldMoment.id.desc())
    return list(db.scalars(stmt).all())


def get_field_moment(
    db: Session,
    *,
    event_id: int,
    moment_id: int,
    actor: User,
) -> FieldMoment:
    if not can_capture_field_moments(actor):
        raise EventServiceError("forbidden", "Эта роль не может смотреть полевые моменты", 403)
    get_event(db, event_id=event_id, actor=actor)
    moment = db.scalar(
        select(FieldMoment).where(FieldMoment.id == moment_id, FieldMoment.event_id == event_id)
    )
    if moment is None:
        raise EventServiceError("not_found", "Момент не найден", 404)
    return moment


def upload_field_moment(
    db: Session,
    *,
    event_id: int,
    actor: User,
    file: UploadFile,
    title: str,
    pov: str = "other",
    heat_id: int | None = None,
    notes: str | None = None,
    repo_root: Path,
    audit_enabled: bool = True,
) -> FieldMoment:
    if not can_capture_field_moments(actor):
        raise EventServiceError("forbidden", "Эта роль не может снимать полевые моменты", 403)

    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    pov_norm = (pov or "other").strip().lower()
    if pov_norm not in ALLOWED_POV:
        raise EventServiceError(
            "invalid_pov",
            "Точка съёмки: бэкстейдж, пилот, маршал, на воде, зрители или другое",
            400,
        )

    if heat_id is not None:
        from app.models.heat import Heat

        heat = db.get(Heat, heat_id)
        if heat is None or heat.event_id != event.id:
            raise EventServiceError("invalid_heat", "Заезд не найден для этого события", 400)

    original = file.filename or "capture.bin"
    safe_name = _safe_filename(original)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise EventServiceError(
            "invalid_file_type",
            "Можно фото JPG/PNG/WebP/HEIC или видео MP4/WebM/MOV",
            400,
        )

    is_video = suffix in ALLOWED_VIDEO
    limit = MAX_VIDEO_BYTES if is_video else MAX_PHOTO_BYTES
    raw = file.file.read(limit + 1)
    if len(raw) == 0:
        raise EventServiceError("empty_file", "Файл пустой", 400)
    if len(raw) > limit:
        mb = limit // (1024 * 1024)
        raise EventServiceError("file_too_large", f"Файл больше {mb} МБ", 400)

    base = _media_base(repo_root)
    event_dir = base / event.slug
    event_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    dest = (event_dir / stored_name).resolve()
    if not str(dest).startswith(str(base)):
        raise EventServiceError("invalid_path", "Некорректный путь файла", 400)
    dest.write_bytes(raw)

    mime = file.content_type or "application/octet-stream"
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".png":
        mime = "image/png"
    elif suffix == ".webp":
        mime = "image/webp"
    elif suffix in {".heic", ".heif"}:
        mime = "image/heic"
    elif suffix == ".mp4":
        mime = "video/mp4"
    elif suffix == ".webm":
        mime = "video/webm"
    elif suffix in {".mov", ".m4v"}:
        mime = "video/quicktime"

    title_clean = (title or "").strip() or POV_TITLES_RU[pov_norm]
    moment = FieldMoment(
        event_id=event.id,
        heat_id=heat_id,
        title=title_clean[:255],
        pov=pov_norm,
        media_kind="video" if is_video else "photo",
        file_name=safe_name,
        relative_path=f"{event.slug}/{stored_name}",
        mime_type=mime,
        byte_size=len(raw),
        notes=(notes or None),
        created_by_user_id=actor.id,
        status="draft",
    )
    db.add(moment)
    db.flush()

    append_audit(
        db,
        action="field_moment.upload",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="field_moment",
        entity_id=str(moment.id),
        payload={
            "event_id": event.id,
            "pov": moment.pov,
            "media_kind": moment.media_kind,
            "bytes": moment.byte_size,
        },
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(moment)
    return moment


def update_field_moment(
    db: Session,
    *,
    event_id: int,
    moment_id: int,
    actor: User,
    data: FieldMomentUpdate,
    audit_enabled: bool = True,
) -> FieldMoment:
    moment = get_field_moment(db, event_id=event_id, moment_id=moment_id, actor=actor)
    event = get_event(db, event_id=event_id, actor=actor)
    assert_event_mutable(event)
    if data.status is not None:
        if data.status not in ALLOWED_STATUSES:
            raise EventServiceError("invalid_status", "Некорректный статус момента", 400)
        if data.status != moment.status and not can_moderate_field_moments(actor):
            raise EventServiceError("forbidden", "Менять статус момента может организатор", 403)
        moment.status = data.status
    if data.title is not None:
        cleaned = data.title.strip()
        if cleaned:
            moment.title = cleaned[:255]
    if data.notes is not None:
        moment.notes = data.notes.strip() or None
    if data.pov is not None:
        pov_norm = data.pov.strip().lower()
        if pov_norm not in ALLOWED_POV:
            raise EventServiceError("invalid_pov", "Некорректная точка съёмки", 400)
        moment.pov = pov_norm

    append_audit(
        db,
        action="field_moment.update",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="field_moment",
        entity_id=str(moment.id),
        payload={"status": moment.status, "pov": moment.pov},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(moment)
    return moment
