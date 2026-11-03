"""Event publications: create, moderate, media upload (ADR-0013)."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.domain.publication_policy import (
    ALLOWED_MEDIA_EXTENSIONS,
    ALLOWED_MEDIA_MIME,
    MAX_MEDIA_BYTES,
    PUBLICATION_TYPES,
    assert_author_role,
    can_create_news,
    can_create_post,
    can_create_type,
    can_moderate,
    can_publish_direct,
    role_of,
)
from app.models.publication import Publication, PublicationMedia
from app.models.user import User
from app.schemas.publication import PublicationCreate, PublicationModerate, PublicationUpdate
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, get_event

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_WEBP_RIFF = b"RIFF"
_WEBP_WEBP = b"WEBP"


def _safe_filename(name: str) -> str:
    base = Path(name or "image").name
    cleaned = re.sub(r"[^\w.\-()+ ]+", "_", base, flags=re.UNICODE).strip(" ._")
    return (cleaned or "image")[:180]


def _publications_base(data_dir: Path) -> Path:
    return (data_dir / "publications").resolve()


def _sniff_image(header: bytes) -> str | None:
    if header.startswith(_JPEG_MAGIC):
        return "image/jpeg"
    if header.startswith(_PNG_MAGIC):
        return "image/png"
    if len(header) >= 12 and header[:4] == _WEBP_RIFF and header[8:12] == _WEBP_WEBP:
        return "image/webp"
    return None


def _to_out_media(item: PublicationMedia, event_id: int) -> dict:
    return {
        "id": item.id,
        "file_name": item.file_name,
        "mime_type": item.mime_type,
        "file_size": item.file_size,
        "sort_order": item.sort_order,
        "download_path": (
            f"/api/v1/events/{event_id}/publications/{item.publication_id}/media/{item.id}/file"
        ),
    }


def publication_to_dict(pub: Publication) -> dict:
    return {
        "id": pub.id,
        "event_id": pub.event_id,
        "author_user_id": pub.author_user_id,
        "author_role": pub.author_role,
        "author_display_name": pub.author_display_name_snapshot,
        "type": pub.type,
        "title": pub.title,
        "body": pub.body,
        "status": pub.status,
        "version": pub.version,
        "moderation_note": pub.moderation_note,
        "published_at": pub.published_at,
        "created_at": pub.created_at,
        "updated_at": pub.updated_at,
        "media": [_to_out_media(m, pub.event_id) for m in (pub.media_items or [])],
    }


def _load_publication(db: Session, *, event_id: int, publication_id: int) -> Publication:
    pub = db.scalar(
        select(Publication)
        .options(selectinload(Publication.media_items))
        .where(Publication.id == publication_id, Publication.event_id == event_id)
    )
    if pub is None:
        raise EventServiceError("not_found", "Publication not found", 404)
    return pub


def _can_view(pub: Publication, actor: User | None) -> bool:
    if pub.status == "published":
        return True
    if actor is None:
        return False
    if can_moderate(actor):
        return True
    return pub.author_user_id == actor.id


def _can_edit(pub: Publication, actor: User) -> bool:
    if pub.status == "void":
        return False
    if can_moderate(actor):
        return True
    return pub.author_user_id == actor.id and pub.status in {
        "draft",
        "pending_moderation",
        "rejected",
    }


def list_publications(
    db: Session,
    *,
    event_id: int,
    actor: User | None,
    status: str | None = None,
) -> list[Publication]:
    get_event(db, event_id=event_id, actor=actor)
    stmt = (
        select(Publication)
        .options(selectinload(Publication.media_items))
        .where(Publication.event_id == event_id)
        .order_by(Publication.id.desc())
    )
    if status:
        stmt = stmt.where(Publication.status == status)
    items = list(db.scalars(stmt).all())
    return [p for p in items if _can_view(p, actor)]


def get_publication(
    db: Session,
    *,
    event_id: int,
    publication_id: int,
    actor: User | None,
) -> Publication:
    get_event(db, event_id=event_id, actor=actor)
    pub = _load_publication(db, event_id=event_id, publication_id=publication_id)
    if not _can_view(pub, actor):
        raise EventServiceError("not_found", "Publication not found", 404)
    return pub


def create_publication(
    db: Session,
    *,
    event_id: int,
    actor: User,
    data: PublicationCreate,
    audit_enabled: bool = True,
) -> Publication:
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)

    pub_type = data.type
    if pub_type not in PUBLICATION_TYPES:
        raise EventServiceError("invalid_type", "type must be post or news", 400)
    if not can_create_type(actor, pub_type):
        raise EventServiceError(
            "forbidden",
            "Недостаточно прав для создания публикации этого типа",
            403,
        )

    try:
        author_role = assert_author_role(actor, data.author_role)
    except ValueError as exc:
        raise EventServiceError("invalid_author_role", "Некорректная роль автора", 400) from exc
    except PermissionError as exc:
        raise EventServiceError(
            "author_role_mismatch",
            "Нельзя публиковать от имени роли, которой у вас нет",
            403,
        ) from exc

    idem = (data.idempotency_key or "").strip() or None
    if idem:
        existing = db.scalar(
            select(Publication)
            .options(selectinload(Publication.media_items))
            .where(
                Publication.event_id == event_id,
                Publication.author_user_id == actor.id,
                Publication.idempotency_key == idem,
            )
        )
        if existing is not None:
            return existing

    if data.intent == "publish":
        if can_publish_direct(actor):
            status = "published"
            published_at: datetime | None = datetime.now(UTC)
        else:
            status = "pending_moderation"
            published_at = None
    else:
        status = "draft"
        published_at = None

    pub = Publication(
        event_id=event_id,
        author_user_id=actor.id,
        author_role=author_role.value,
        author_display_name_snapshot=actor.display_name or actor.email,
        type=pub_type,
        title=data.title.strip(),
        body=(data.body or "").strip(),
        status=status,
        version=1,
        idempotency_key=idem,
        published_at=published_at,
    )
    db.add(pub)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        # Race on idempotency
        if idem:
            again = db.scalar(
                select(Publication)
                .options(selectinload(Publication.media_items))
                .where(
                    Publication.event_id == event_id,
                    Publication.author_user_id == actor.id,
                    Publication.idempotency_key == idem,
                )
            )
            if again is not None:
                return again
        raise EventServiceError("conflict", "Не удалось создать публикацию", 409) from exc

    append_audit(
        db,
        action="publication.create",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="publication",
        entity_id=str(pub.id),
        payload={"event_id": event_id, "type": pub_type, "status": status},
        enabled=audit_enabled,
    )
    db.commit()
    return _load_publication(db, event_id=event_id, publication_id=pub.id)


def update_publication(
    db: Session,
    *,
    event_id: int,
    publication_id: int,
    actor: User,
    data: PublicationUpdate,
    audit_enabled: bool = True,
) -> Publication:
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    pub = _load_publication(db, event_id=event_id, publication_id=publication_id)
    if not _can_edit(pub, actor):
        raise EventServiceError("forbidden", "Нельзя редактировать эту публикацию", 403)

    if data.type is not None:
        if not can_create_type(actor, data.type) and not can_moderate(actor):
            raise EventServiceError("forbidden", "Недостаточно прав для смены типа", 403)
        pub.type = data.type
    if data.title is not None:
        pub.title = data.title.strip()
    if data.body is not None:
        pub.body = data.body.strip()
    pub.version = int(pub.version or 1) + 1
    db.add(pub)
    append_audit(
        db,
        action="publication.update",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="publication",
        entity_id=str(pub.id),
        payload={"version": pub.version},
        enabled=audit_enabled,
    )
    db.commit()
    return _load_publication(db, event_id=event_id, publication_id=pub.id)


def moderate_publication(
    db: Session,
    *,
    event_id: int,
    publication_id: int,
    actor: User,
    data: PublicationModerate,
    audit_enabled: bool = True,
) -> Publication:
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    if not can_moderate(actor):
        raise EventServiceError("forbidden", "Недостаточно прав для модерации", 403)

    pub = _load_publication(db, event_id=event_id, publication_id=publication_id)
    if data.action == "publish":
        if pub.status not in {"draft", "pending_moderation", "rejected"}:
            raise EventServiceError("invalid_status", "Публикацию нельзя опубликовать", 400)
        pub.status = "published"
        pub.published_at = datetime.now(UTC)
        pub.moderation_note = data.note
    elif data.action == "reject":
        if pub.status not in {"draft", "pending_moderation", "published"}:
            raise EventServiceError("invalid_status", "Публикацию нельзя отклонить", 400)
        pub.status = "rejected"
        pub.published_at = None
        pub.moderation_note = data.note
    elif data.action == "void":
        pub.status = "void"
        pub.moderation_note = data.note
    else:
        raise EventServiceError("invalid_action", "Неизвестное действие модерации", 400)

    pub.version = int(pub.version or 1) + 1
    db.add(pub)
    append_audit(
        db,
        action=f"publication.{data.action}",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="publication",
        entity_id=str(pub.id),
        payload={"status": pub.status},
        enabled=audit_enabled,
    )
    db.commit()
    return _load_publication(db, event_id=event_id, publication_id=pub.id)


def delete_publication(
    db: Session,
    *,
    event_id: int,
    publication_id: int,
    actor: User,
    audit_enabled: bool = True,
) -> None:
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    pub = _load_publication(db, event_id=event_id, publication_id=publication_id)
    is_author = pub.author_user_id == actor.id
    if not (can_moderate(actor) or (is_author and pub.status in {"draft", "rejected", "pending_moderation"})):
        raise EventServiceError("forbidden", "Нельзя удалить эту публикацию", 403)

    append_audit(
        db,
        action="publication.delete",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="publication",
        entity_id=str(pub.id),
        payload={"status": pub.status},
        enabled=audit_enabled,
    )
    db.delete(pub)
    db.commit()


def add_publication_media(
    db: Session,
    *,
    event_id: int,
    publication_id: int,
    actor: User,
    file: UploadFile,
    data_dir: Path,
    audit_enabled: bool = True,
) -> Publication:
    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    pub = _load_publication(db, event_id=event_id, publication_id=publication_id)
    if not _can_edit(pub, actor):
        raise EventServiceError("forbidden", "Нельзя добавлять медиа к этой публикации", 403)

    raw_name = file.filename or "image.jpg"
    ext = Path(raw_name).suffix.lower()
    if ext not in ALLOWED_MEDIA_EXTENSIONS:
        raise EventServiceError(
            "invalid_file_type",
            f"Допустимы: {', '.join(sorted(ALLOWED_MEDIA_EXTENSIONS))}",
            400,
        )

    content = file.file.read(MAX_MEDIA_BYTES + 1)
    if len(content) > MAX_MEDIA_BYTES:
        raise EventServiceError("file_too_large", "Максимальный размер изображения — 10 МБ", 400)
    if not content:
        raise EventServiceError("empty_file", "Пустой файл", 400)

    sniffed = _sniff_image(content[:32])
    if sniffed is None or sniffed not in ALLOWED_MEDIA_MIME:
        raise EventServiceError("invalid_file_content", "Файл не является допустимым изображением", 400)

    safe = _safe_filename(raw_name)
    rel_dir = Path(event.slug) / f"pub_{pub.id}"
    store_name = f"{uuid.uuid4().hex}{ext}"
    base = _publications_base(data_dir)
    target_dir = base / rel_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / store_name
    target_path.write_bytes(content)

    sort_order = len(pub.media_items or [])
    media = PublicationMedia(
        publication_id=pub.id,
        relative_path=str(rel_dir / store_name).replace("\\", "/"),
        file_name=safe,
        mime_type=sniffed,
        file_size=len(content),
        sort_order=sort_order,
    )
    db.add(media)
    pub.version = int(pub.version or 1) + 1
    db.add(pub)
    append_audit(
        db,
        action="publication.media_upload",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="publication",
        entity_id=str(pub.id),
        payload={"mime": sniffed, "size": len(content)},
        enabled=audit_enabled,
    )
    db.commit()
    return _load_publication(db, event_id=event_id, publication_id=pub.id)


def resolve_media_path(
    db: Session,
    *,
    event_id: int,
    publication_id: int,
    media_id: int,
    actor: User | None,
    data_dir: Path,
) -> tuple[PublicationMedia, Path]:
    get_event(db, event_id=event_id, actor=actor)
    pub = _load_publication(db, event_id=event_id, publication_id=publication_id)
    if not _can_view(pub, actor):
        raise EventServiceError("not_found", "Publication not found", 404)
    media = next((m for m in pub.media_items if m.id == media_id), None)
    if media is None:
        raise EventServiceError("not_found", "Media not found", 404)

    base = _publications_base(data_dir)
    path = (base / media.relative_path).resolve()
    if not str(path).startswith(str(base)):
        raise EventServiceError("invalid_path", "Invalid media path", 400)
    if not path.is_file():
        raise EventServiceError("file_missing", "Файл недоступен на сервере", 404)
    return media, path


def publishable_author_roles_for(user: User) -> list[str]:
    """Roles the UI may offer — only the actor's current role if capable."""
    role = role_of(user)
    if can_create_post(user) or can_create_news(user):
        return [role.value]
    return []
