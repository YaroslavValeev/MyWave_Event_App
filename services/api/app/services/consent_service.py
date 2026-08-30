"""Consent grant/revoke and public-name policy."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.domain.consent import (
    ALL_PURPOSES,
    CATALOG,
    OPTIONAL_PURPOSES,
    PURPOSE_ANALYTICS,
    PURPOSE_PRIVACY,
    PURPOSE_PUBLISH,
    PURPOSE_TERMS,
    REQUIRED_PURPOSES,
    get_document,
)
from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.models.consent import ConsentRecord
from app.models.participant import Participant
from app.models.user import User
from app.services.audit_service import append_audit


class ConsentError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def active_consent(db: Session, *, user_id: int, purpose: str) -> ConsentRecord | None:
    return db.scalar(
        select(ConsentRecord)
        .where(
            ConsentRecord.user_id == user_id,
            ConsentRecord.purpose == purpose,
            ConsentRecord.revoked_at.is_(None),
        )
        .order_by(ConsentRecord.id.desc())
    )


def has_active_consent(db: Session, *, user_id: int, purpose: str) -> bool:
    return active_consent(db, user_id=user_id, purpose=purpose) is not None


def list_user_consents(db: Session, *, user_id: int) -> list[ConsentRecord]:
    rows: list[ConsentRecord] = []
    for purpose in ALL_PURPOSES:
        row = active_consent(db, user_id=user_id, purpose=purpose)
        if row is not None:
            rows.append(row)
    return rows


def grant_consent(
    db: Session,
    *,
    user: User,
    purpose: str,
    source: str,
    settings: Settings,
    version: str | None = None,
) -> ConsentRecord:
    doc = get_document(purpose)
    if doc is None:
        raise ConsentError("unknown_purpose", "Неизвестный тип согласия", status_code=400)
    expected = version or doc.version
    if expected != doc.version:
        raise ConsentError(
            "version_mismatch",
            "Версия документа устарела. Обновите страницу и примите актуальную редакцию.",
            status_code=409,
        )
    existing = active_consent(db, user_id=user.id, purpose=purpose)
    if existing is not None and existing.version == doc.version:
        return existing
    if existing is not None:
        existing.revoked_at = _now()
        db.add(existing)

    row = ConsentRecord(
        user_id=user.id,
        purpose=purpose,
        version=doc.version,
        source=source,
        granted_at=_now(),
    )
    db.add(row)
    db.flush()
    append_audit(
        db,
        action="consent.granted",
        actor_user_id=user.id,
        actor_email=user.email,
        entity_type="consent",
        entity_id=str(row.id),
        payload={"purpose": purpose, "version": doc.version, "source": source},
        enabled=settings.enable_audit_log,
    )
    return row


def revoke_consent(
    db: Session,
    *,
    user: User,
    purpose: str,
    settings: Settings,
) -> ConsentRecord:
    doc = get_document(purpose)
    if doc is None:
        raise ConsentError("unknown_purpose", "Неизвестный тип согласия", status_code=400)
    if purpose in REQUIRED_PURPOSES:
        raise ConsentError(
            "consent_locked",
            "Обязательное согласие нельзя отозвать, пока аккаунт используется. "
            "Обратитесь к организатору для удаления аккаунта.",
            status_code=409,
        )
    if purpose not in OPTIONAL_PURPOSES:
        raise ConsentError("unknown_purpose", "Неизвестный тип согласия", status_code=400)
    row = active_consent(db, user_id=user.id, purpose=purpose)
    if row is None:
        raise ConsentError("consent_missing", "Активное согласие не найдено", status_code=404)
    row.revoked_at = _now()
    db.add(row)
    append_audit(
        db,
        action="consent.revoked",
        actor_user_id=user.id,
        actor_email=user.email,
        entity_type="consent",
        entity_id=str(row.id),
        payload={"purpose": purpose, "version": row.version},
        enabled=settings.enable_audit_log,
    )
    db.flush()
    return row


def grant_registration_consents(
    db: Session,
    *,
    user: User,
    accept_terms: bool,
    accept_privacy: bool,
    accept_publish_name: bool,
    accept_analytics: bool,
    settings: Settings,
) -> None:
    if not accept_terms or not accept_privacy:
        raise ConsentError(
            "consent_required",
            "Нужно принять пользовательское соглашение и политику конфиденциальности.",
            status_code=400,
        )
    grant_consent(db, user=user, purpose=PURPOSE_TERMS, source="register", settings=settings)
    grant_consent(db, user=user, purpose=PURPOSE_PRIVACY, source="register", settings=settings)
    if accept_publish_name:
        grant_consent(db, user=user, purpose=PURPOSE_PUBLISH, source="register", settings=settings)
    if accept_analytics:
        grant_consent(db, user=user, purpose=PURPOSE_ANALYTICS, source="register", settings=settings)


def public_participant_name(db: Session, participant: Participant, actor: User | None) -> str:
    """Mask self-serve names without publish consent. Organizer imports stay visible."""
    privileged = False
    if actor is not None:
        try:
            privileged = Role(actor.role) in EVENT_WRITE_ROLES
        except ValueError:
            privileged = False
    if privileged:
        return participant.full_name
    if participant.source_row is not None:
        return participant.full_name
    if participant.user_id and has_active_consent(
        db, user_id=participant.user_id, purpose=PURPOSE_PUBLISH
    ):
        return participant.full_name
    return f"Участник №{participant.id}"
