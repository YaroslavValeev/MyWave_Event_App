"""Import Center: parse → match → review → commit. No PII in logs."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.athlete import AccountAthleteLink, AthleteContact, AthleteProfile
from app.models.category import Category
from app.models.event import Event
from app.models.importing import ImportBatch, ImportRow
from app.models.participant import Participant
from app.models.user import User
from app.services.athlete_id_service import allocate_athlete_id
from app.services.audit_service import append_audit
from app.services.event_service import can_write_events, get_event
from app.services.import_parse import (
    ParsedRow,
    content_sha256,
    dump_raw,
    normalize_fio,
    parse_registration_workbook,
)
from app.services.phone_utils import mask_phone


class ImportServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


AUTO_APPROVE = frozenset({"new", "exact"})
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def _slugify(value: str) -> str:
    ascii_bits = re.sub(r"[^a-z0-9]+", "-", value.lower())
    ascii_bits = re.sub(r"-+", "-", ascii_bits).strip("-")[:40]
    return ascii_bits or "cat"


def _get_or_create_category(db: Session, event: Event, discipline: str, cat_title: str) -> Category:
    code = f"{_slugify(discipline)}-{_slugify(cat_title)}"[:120]
    existing = db.scalar(
        select(Category).where(Category.event_id == event.id, Category.code == code)
    )
    if existing:
        return existing
    cat = Category(event_id=event.id, code=code, title=cat_title, discipline=discipline)
    db.add(cat)
    db.flush()
    return cat


def _profiles_index(db: Session) -> tuple[dict[str, AthleteProfile], dict[str, list[AthleteProfile]]]:
    profiles = list(db.scalars(select(AthleteProfile)).all())
    by_id = {p.id: p for p in profiles}
    by_fio: dict[str, AthleteProfile] = {normalize_fio(p.display_name): p for p in profiles}
    by_phone: dict[str, list[AthleteProfile]] = {}
    for contact in db.scalars(select(AthleteContact)).all():
        profile = by_id.get(contact.athlete_profile_id)
        if profile:
            by_phone.setdefault(contact.phone_e164, []).append(profile)
    return by_fio, by_phone


def _classify(parsed: ParsedRow, by_fio: dict[str, AthleteProfile], by_phone: dict[str, list[AthleteProfile]]) -> tuple[str, int, list[str], int | None]:
    codes: list[str] = []
    if not parsed.display_name:
        return "excluded", 0, ["empty_name"], None
    if not parsed.discipline:
        codes.append("unknown_discipline")
    if not parsed.category_label:
        codes.append("unknown_category")
    if not parsed.has_medical:
        codes.append("missing_document")

    fio_key = normalize_fio(parsed.display_name)
    profile = by_fio.get(fio_key)
    phone_hits = by_phone.get(parsed.phone_e164 or "", [])
    phone_hits = [p for p in phone_hits if p is not None]

    if profile and parsed.birth_year and profile.birth_year and profile.birth_year != parsed.birth_year:
        codes.append("dob_conflict")
        return "conflict", 40, codes, profile.id

    if profile and parsed.phone_e164:
        owns = any(p.id == profile.id for p in phone_hits)
        if phone_hits and not owns:
            codes.append("phone_conflict")
            return "conflict", 40, codes, profile.id
        return "exact", 95, codes, profile.id

    if profile and parsed.birth_year and profile.birth_year == parsed.birth_year:
        return "probable", 70, codes, profile.id

    if profile:
        return "probable", 55, codes, profile.id

    if phone_hits:
        names = {normalize_fio(p.display_name) for p in phone_hits}
        if fio_key not in names:
            codes.append("phone_conflict")
            return "conflict", 35, codes, phone_hits[0].id
        return "exact", 90, codes, phone_hits[0].id

    kind = "conflict" if "unknown_discipline" in codes else "new"
    return kind, 20 if kind == "new" else 30, codes, None


def create_or_reuse_batch(
    db: Session,
    *,
    event_id: int,
    actor: User,
    filename: str,
    payload: bytes,
    audit_enabled: bool = True,
) -> ImportBatch:
    if not can_write_events(actor):
        raise ImportServiceError("forbidden", "Импорт доступен организатору", 403)
    event = get_event(db, event_id=event_id, actor=actor)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise ImportServiceError("file_too_large", "Файл больше 5 МБ", 400)
    name = (filename or "upload.xlsx").lower()
    if not name.endswith(".xlsx"):
        raise ImportServiceError("invalid_type", "Нужен файл .xlsx", 400)

    digest = content_sha256(payload)
    existing = db.scalar(
        select(ImportBatch).where(ImportBatch.event_id == event.id, ImportBatch.content_sha256 == digest)
    )
    if existing:
        return existing

    try:
        kind, parsed_rows = parse_registration_workbook(payload)
    except Exception as exc:
        raise ImportServiceError("parse_failed", "Не удалось прочитать таблицу", 400) from exc

    by_fio, by_phone = _profiles_index(db)
    batch = ImportBatch(
        event_id=event.id,
        source_filename=filename[:255],
        source_kind=kind,
        content_sha256=digest,
        status="parsed",
        uploaded_by_user_id=actor.id,
    )
    db.add(batch)
    db.flush()

    counts = {"new": 0, "exact": 0, "probable": 0, "conflict": 0, "excluded": 0}
    seen_in_file: set[tuple[str, str | None]] = set()
    for parsed in parsed_rows:
        key = (normalize_fio(parsed.display_name or ""), parsed.discipline)
        extra: list[str] = []
        if parsed.display_name and key in seen_in_file:
            extra.append("repeat_application")
        if parsed.display_name:
            seen_in_file.add(key)
        match_kind, confidence, codes, profile_id = _classify(parsed, by_fio, by_phone)
        codes = list(dict.fromkeys(codes + extra))
        if "repeat_application" in extra and match_kind == "new":
            match_kind = "probable"
        decision = "approve" if match_kind in AUTO_APPROVE and "phone_conflict" not in codes else "pending"
        if match_kind == "excluded":
            decision = "reject"
        row = ImportRow(
            batch_id=batch.id,
            source_sheet=parsed.source_sheet[:128],
            source_row=parsed.source_row,
            raw_json=dump_raw(parsed),
            normalized_fio=normalize_fio(parsed.display_name) if parsed.display_name else None,
            display_name=parsed.display_name,
            latin_name=parsed.latin_name,
            phone_e164=parsed.phone_e164,
            birth_year=parsed.birth_year,
            region=parsed.region,
            discipline=parsed.discipline,
            category_label=parsed.category_label,
            has_medical=parsed.has_medical,
            match_kind=match_kind,
            confidence=confidence,
            conflict_codes=",".join(codes),
            athlete_profile_id=profile_id,
            admin_decision=decision,
        )
        db.add(row)
        counts[match_kind] = counts.get(match_kind, 0) + 1

    batch.row_count = sum(counts.values())
    batch.new_count = counts["new"]
    batch.exact_count = counts["exact"]
    batch.probable_count = counts["probable"]
    batch.conflict_count = counts["conflict"]
    batch.excluded_count = counts["excluded"]
    db.add(batch)
    db.flush()
    append_audit(
        db,
        action="import.batch.parse",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="import_batch",
        entity_id=str(batch.id),
        payload={"rows": batch.row_count, "kind": kind, "sha": digest[:12]},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(batch)
    return batch


def list_batches(db: Session, *, event_id: int, actor: User) -> list[ImportBatch]:
    if not can_write_events(actor):
        raise ImportServiceError("forbidden", "Импорт доступен организатору", 403)
    get_event(db, event_id=event_id, actor=actor)
    return list(
        db.scalars(
            select(ImportBatch).where(ImportBatch.event_id == event_id).order_by(ImportBatch.id.desc())
        ).all()
    )


def get_batch(db: Session, *, event_id: int, batch_id: int, actor: User) -> ImportBatch:
    if not can_write_events(actor):
        raise ImportServiceError("forbidden", "Импорт доступен организатору", 403)
    get_event(db, event_id=event_id, actor=actor)
    batch = db.get(ImportBatch, batch_id)
    if batch is None or batch.event_id != event_id:
        raise ImportServiceError("not_found", "Пакет импорта не найден", 404)
    return batch


def list_rows(db: Session, *, batch_id: int) -> list[ImportRow]:
    return list(db.scalars(select(ImportRow).where(ImportRow.batch_id == batch_id).order_by(ImportRow.id)).all())


def decide_row(
    db: Session,
    *,
    event_id: int,
    batch_id: int,
    row_id: int,
    actor: User,
    decision: str,
) -> ImportRow:
    if decision not in {"approve", "reject"}:
        raise ImportServiceError("invalid_decision", "decision: approve|reject", 400)
    batch = get_batch(db, event_id=event_id, batch_id=batch_id, actor=actor)
    if batch.status == "committed":
        raise ImportServiceError("already_committed", "Пакет уже зафиксирован", 409)
    row = db.get(ImportRow, row_id)
    if row is None or row.batch_id != batch.id:
        raise ImportServiceError("not_found", "Строка не найдена", 404)
    row.admin_decision = decision
    row.decided_by_user_id = actor.id
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _ensure_profile(db: Session, row: ImportRow) -> AthleteProfile:
    if row.athlete_profile_id:
        profile = db.get(AthleteProfile, row.athlete_profile_id)
        if profile:
            return profile
    assert row.display_name
    profile = AthleteProfile(
        athlete_id=allocate_athlete_id(db),
        display_name=row.display_name,
        latin_name=row.latin_name,
        birth_year=row.birth_year,
        region=row.region,
    )
    db.add(profile)
    db.flush()
    if row.phone_e164:
        db.add(
            AthleteContact(
                athlete_profile_id=profile.id,
                phone_e164=row.phone_e164,
                kind="self",
            )
        )
        db.flush()
    row.athlete_profile_id = profile.id
    return profile


def _ensure_pending_account(db: Session, profile: AthleteProfile, phone: str | None) -> User | None:
    if not phone:
        return None
    user = db.scalar(select(User).where(User.phone == phone))
    if user is None:
        from app.services.auth_service import get_user_by_email

        holder = db.scalar(select(User.id).where(User.athlete_id == profile.athlete_id))
        account_id = profile.athlete_id if holder is None else allocate_athlete_id(db)
        email = f"pending.{profile.athlete_id.lower()}@pending.mywave.local"
        if get_user_by_email(db, email) is not None:
            email = f"pending.{account_id.lower()}@pending.mywave.local"
        user = User(
            email=email,
            phone=phone,
            display_name=profile.display_name,
            role="participant",
            status="pending_claim",
            athlete_id=account_id,
        )
        db.add(user)
        db.flush()
    else:
        if not user.athlete_id:
            holder = db.scalar(select(User.id).where(User.athlete_id == profile.athlete_id))
            if holder is None:
                user.athlete_id = profile.athlete_id
                db.add(user)
                db.flush()
    existing = db.scalar(
        select(AccountAthleteLink).where(
            AccountAthleteLink.user_id == user.id,
            AccountAthleteLink.athlete_profile_id == profile.id,
        )
    )
    if existing is None:
        db.add(
            AccountAthleteLink(
                user_id=user.id,
                athlete_profile_id=profile.id,
                relation="self",
                status="pending_claim",
            )
        )
        db.flush()
    return user


def commit_batch(
    db: Session,
    *,
    event_id: int,
    batch_id: int,
    actor: User,
    audit_enabled: bool = True,
) -> ImportBatch:
    batch = get_batch(db, event_id=event_id, batch_id=batch_id, actor=actor)
    if batch.status == "committed":
        return batch
    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    rows = list_rows(db, batch_id=batch.id)
    committed = 0
    for row in rows:
        if row.admin_decision != "approve":
            continue
        if not row.display_name:
            continue
        profile = _ensure_profile(db, row)
        _ensure_pending_account(db, profile, row.phone_e164)
        discipline = row.discipline or "unknown"
        cat_title = row.category_label or "Без категории"
        category = _get_or_create_category(db, event, discipline, cat_title)
        already = db.scalar(
            select(Participant).where(
                Participant.event_id == event.id,
                Participant.athlete_profile_id == profile.id,
                Participant.category_id == category.id,
            )
        )
        if already is None:
            participant = Participant(
                event_id=event.id,
                category_id=category.id,
                athlete_profile_id=profile.id,
                full_name=row.display_name,
                birth_year=row.birth_year,
                region=row.region,
                phone=row.phone_e164,
                has_medical_cert=row.has_medical,
                status="registered",
                source_row=row.source_row,
            )
            db.add(participant)
            db.flush()
            row.participant_id = participant.id
        else:
            row.participant_id = already.id
        db.add(row)
        committed += 1

    batch.committed_count = committed
    batch.status = "committed"
    batch.committed_at = datetime.now(timezone.utc)
    db.add(batch)
    append_audit(
        db,
        action="import.batch.commit",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="import_batch",
        entity_id=str(batch.id),
        payload={"committed": committed},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(batch)
    return batch


def row_public_dict(row: ImportRow) -> dict:
    return {
        "id": row.id,
        "source_sheet": row.source_sheet,
        "source_row": row.source_row,
        "display_name": row.display_name,
        "phone_masked": mask_phone(row.phone_e164),
        "birth_year": row.birth_year,
        "region": row.region,
        "discipline": row.discipline,
        "category_label": row.category_label,
        "has_medical": row.has_medical,
        "match_kind": row.match_kind,
        "confidence": row.confidence,
        "conflict_codes": [c for c in row.conflict_codes.split(",") if c],
        "admin_decision": row.admin_decision,
        "athlete_profile_id": row.athlete_profile_id,
        "participant_id": row.participant_id,
    }


def batch_public_dict(batch: ImportBatch, rows: list[ImportRow] | None = None) -> dict:
    payload = {
        "id": batch.id,
        "event_id": batch.event_id,
        "source_filename": batch.source_filename,
        "source_kind": batch.source_kind,
        "status": batch.status,
        "row_count": batch.row_count,
        "new_count": batch.new_count,
        "exact_count": batch.exact_count,
        "probable_count": batch.probable_count,
        "conflict_count": batch.conflict_count,
        "excluded_count": batch.excluded_count,
        "committed_count": batch.committed_count,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "committed_at": batch.committed_at.isoformat() if batch.committed_at else None,
    }
    if rows is not None:
        payload["rows"] = [row_public_dict(r) for r in rows]
    return payload
