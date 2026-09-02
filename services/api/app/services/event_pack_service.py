"""Ingest owner documents into one Kazan event: roster, officials, heats, files."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.athlete import AthleteProfile
from app.models.category import Category
from app.models.document import Document
from app.models.event import Event
from app.models.heat import Heat, Run, StartListEntry
from app.models.participant import Participant
from app.models.user import User
from app.services.athlete_id_service import allocate_athlete_id
from app.services.audit_service import append_audit
from app.services.category_canon import canonical_category
from app.services.document_service import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES
from app.services.event_service import EventServiceError, can_write_events, get_event
from app.services.heat_service import clear_start_list
from app.services.import_service import (
    ImportServiceError,
    commit_batch,
    create_or_reuse_batch,
    list_rows,
)
from app.services.official_service import replace_officials
from app.services.officials_parse import parse_ks_protocol_text
from app.services.pdf_text import extract_pdf_text
from app.services.schedule_parse import parse_schedule_workbook
from app.services.startlist_parse import ParsedStartHeat, parse_startlist_text


class PackIngestError(EventServiceError):
    pass


def _latin_key(value: str | None) -> str:
    if not value:
        return ""
    text = value.replace("_", " ").replace("*", "")
    key = re.sub(r"[^a-z0-9]+", "", text.casefold())
    return key.replace("georgiy", "georgii")


def _store_document(
    db: Session,
    *,
    event: Event,
    actor: User,
    filename: str,
    payload: bytes,
    title: str,
    kind: str,
    access_class: str,
    description: str | None,
    repo_root: Path,
    audit_enabled: bool,
) -> Document:
    digest = hashlib.sha256(payload).hexdigest()
    existing = db.scalar(
        select(Document).where(Document.event_id == event.id, Document.content_sha256 == digest)
    )
    if existing:
        return existing
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise PackIngestError("invalid_file_type", "Allowed types: .pdf, .xlsx, .xls, .docx", 400)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise PackIngestError("file_too_large", "File exceeds 25 MB", 400)
    dest_dir = (repo_root / "data" / "documents" / event.slug).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\-()+ ]+", "_", Path(filename).name, flags=re.UNICODE).strip(" ._")[:180]
    stored = f"{uuid.uuid4().hex[:12]}_{safe or 'file'}"
    (dest_dir / stored).write_bytes(payload)
    doc = Document(
        event_id=event.id,
        title=title[:255],
        kind=kind,
        language="ru",
        file_name=safe or stored,
        relative_path=f"{event.slug}/{stored}",
        description=description,
        access_class=access_class,
        content_sha256=digest,
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
        payload={"event_id": event.id, "kind": kind, "title": title},
        enabled=audit_enabled,
    )
    return doc


def _get_or_create_canon_category(
    db: Session, event: Event, *, discipline: str, label: str, birth_year: int | None = None, sex_hint: str | None = None
) -> Category:
    canon = canonical_category(label, discipline=discipline, birth_year=birth_year, sex_hint=sex_hint)
    existing = db.scalar(select(Category).where(Category.event_id == event.id, Category.code == canon.code))
    if existing:
        return existing
    cat = Category(
        event_id=event.id,
        code=canon.code,
        title=canon.title,
        discipline=discipline,
        notes=f"iwwf={canon.iwwf_class}; source={label}" if label else f"iwwf={canon.iwwf_class}",
    )
    db.add(cat)
    db.flush()
    return cat


def _upsert_heat(
    db: Session,
    *,
    event: Event,
    code: str,
    title: str,
    heat_number: int,
    category: Category | None,
    scheduled_at: datetime | None,
    notes: str | None,
) -> Heat:
    heat = db.scalar(select(Heat).where(Heat.event_id == event.id, Heat.code == code))
    if heat is None:
        heat = Heat(
            event_id=event.id,
            code=code[:64],
            title=title[:255],
            heat_number=heat_number,
            category_id=category.id if category else None,
            scheduled_at=scheduled_at,
            status="planned",
            notes=notes,
        )
        db.add(heat)
        db.flush()
        return heat
    heat.title = title[:255]
    heat.heat_number = heat_number
    if category is not None:
        heat.category_id = category.id
    if scheduled_at is not None:
        heat.scheduled_at = scheduled_at
    if notes:
        heat.notes = notes
    db.flush()
    return heat


def _match_participant(
    db: Session,
    *,
    event: Event,
    category: Category,
    latin_name: str,
) -> Participant | None:
    want = _latin_key(latin_name)
    if not want:
        return None
    parts = list(
        db.scalars(
            select(Participant).where(
                Participant.event_id == event.id,
                Participant.category_id == category.id,
            )
        ).all()
    )
    for part in parts:
        profile = db.get(AthleteProfile, part.athlete_profile_id) if part.athlete_profile_id else None
        candidates = [part.full_name, profile.latin_name if profile else None, profile.display_name if profile else None]
        if any(_latin_key(c) == want for c in candidates if c):
            return part
    # fallback: same event any category, latin exact
    all_parts = list(db.scalars(select(Participant).where(Participant.event_id == event.id)).all())
    for part in all_parts:
        profile = db.get(AthleteProfile, part.athlete_profile_id) if part.athlete_profile_id else None
        latin = profile.latin_name if profile else None
        if _latin_key(latin) == want:
            return part
    return None


def _ensure_startlist_participant(
    db: Session,
    *,
    event: Event,
    category: Category,
    latin_name: str,
) -> Participant:
    found = _match_participant(db, event=event, category=category, latin_name=latin_name)
    if found:
        return found
    profile = AthleteProfile(
        athlete_id=allocate_athlete_id(db),
        display_name=latin_name,
        latin_name=latin_name,
    )
    db.add(profile)
    db.flush()
    part = Participant(
        event_id=event.id,
        category_id=category.id,
        athlete_profile_id=profile.id,
        full_name=latin_name,
        status="registered",
    )
    db.add(part)
    db.flush()
    return part


def _apply_start_heat(db: Session, event: Event, parsed: ParsedStartHeat, heat_number: int) -> tuple[Heat, int]:
    label = f"{parsed.age_key} {parsed.sex}"
    category = _get_or_create_canon_category(
        db,
        event,
        discipline=parsed.discipline,
        label=label,
        sex_hint=parsed.sex,
    )
    hour, minute = (int(x) for x in parsed.time_hm.split(":"))
    scheduled = datetime(parsed.year, parsed.month, parsed.day, hour, minute, tzinfo=timezone.utc)
    code = f"d1-{category.code}-qual1"[:64]
    notes = (
        f"source=iwwf_startlist; original={parsed.title}; "
        f"homologation={parsed.homologation or 'unknown'}"
    )
    heat = _upsert_heat(
        db,
        event=event,
        code=code,
        title=f"{category.title} · квалификация",
        heat_number=heat_number,
        category=category,
        scheduled_at=scheduled,
        notes=notes,
    )
    clear_start_list(db, heat_id=heat.id)
    added = 0
    for starter in parsed.starters:
        part = _ensure_startlist_participant(db, event=event, category=category, latin_name=starter.latin_name)
        entry = StartListEntry(
            heat_id=heat.id,
            event_id=event.id,
            participant_id=part.id,
            start_order=starter.start_order,
            status="scheduled",
            notes=starter.latin_name,
        )
        db.add(entry)
        db.flush()
        db.add(
            Run(
                event_id=event.id,
                heat_id=heat.id,
                start_list_entry_id=entry.id,
                participant_id=part.id,
                attempt_no=1,
                status="scheduled",
            )
        )
        added += 1
    db.flush()
    return heat, added


def _apply_schedule(db: Session, event: Event, payload: bytes) -> int:
    rows = parse_schedule_workbook(payload)
    created = 0
    for idx, row in enumerate(rows, start=1):
        category = _get_or_create_canon_category(
            db, event, discipline=row.discipline, label=row.category_title
        )
        disc_slug = category.code  # wb-u14-f
        code = f"d{row.day_no}-{disc_slug}-{row.round_key}{row.heat_index}"[:64]
        hour, minute = (int(x) for x in row.time_from.split(":"))
        scheduled = datetime(
            row.day_date.year, row.day_date.month, row.day_date.day, hour, minute, tzinfo=timezone.utc
        )
        _upsert_heat(
            db,
            event=event,
            code=code,
            title=f"{category.title} · {row.round_label}",
            heat_number=100 + idx,
            category=category,
            scheduled_at=scheduled,
            notes=f"source=excel_schedule; athletes_planned={row.athlete_count}",
        )
        created += 1
    return created


def _remap_existing_to_iwwf(db: Session, event: Event) -> int:
    """Re-point already imported participants to IWWF codes without duplicating rows."""
    parts = list(db.scalars(select(Participant).where(Participant.event_id == event.id)).all())
    changed = 0
    for part in parts:
        old = db.get(Category, part.category_id) if part.category_id else None
        source = None
        if old and old.notes:
            match = re.search(r"source=([^;]+)", old.notes)
            if match:
                source = match.group(1).strip()
        if not source and old:
            source = old.title
        if not source:
            continue
        cat = _get_or_create_canon_category(
            db,
            event,
            discipline=old.discipline if old else "Wakeboard (boat)",
            label=source,
            birth_year=part.birth_year,
        )
        if part.category_id != cat.id:
            part.category_id = cat.id
            db.add(part)
            changed += 1
    db.flush()
    return changed


def _ingest_xlsx(
    db: Session,
    *,
    event: Event,
    actor: User,
    filename: str,
    payload: bytes,
    repo_root: Path,
    audit_enabled: bool,
) -> dict:
    batch = create_or_reuse_batch(
        db,
        event_id=event.id,
        actor=actor,
        filename=filename,
        payload=payload,
        audit_enabled=audit_enabled,
    )
    if batch.status != "committed":
        for row in list_rows(db, batch_id=batch.id):
            if row.admin_decision != "reject" and row.match_kind != "excluded":
                row.admin_decision = "approve"
                db.add(row)
        db.flush()
        batch = commit_batch(
            db, event_id=event.id, batch_id=batch.id, actor=actor, audit_enabled=audit_enabled
        )
    doc = _store_document(
        db,
        event=event,
        actor=actor,
        filename=filename,
        payload=payload,
        title="Реестр заявок ЧР/ПР 2026 (категории)",
        kind="questionnaire",
        access_class="admin-only",
        description="PII; не публиковать. Категории приведены к IWWF (ADR-0007).",
        repo_root=repo_root,
        audit_enabled=audit_enabled,
    )
    schedule_heats = _apply_schedule(db, event, payload)
    remapped = _remap_existing_to_iwwf(db, event)
    return {
        "kind": "registration",
        "batch_id": batch.id,
        "committed": batch.committed_count,
        "document_id": doc.id,
        "schedule_heats": schedule_heats,
        "remapped": remapped,
    }


def _classify_pdf(filename: str, text: str) -> str:
    name = filename.casefold()
    if "startlist" in name or "starting list" in text.casefold():
        return "start_list"
    if "32_" in name or ("протокол" in name and "кс" in name):
        return "official_appointment"
    folded = text.casefold()
    if "starting list" in folded:
        return "start_list"
    if "коллегии спортивных судей" in folded or "32-кс" in folded:
        return "official_appointment"
    return "other"


def ingest_pack(
    db: Session,
    *,
    event_id: int,
    actor: User,
    files: list[tuple[str, bytes]],
    repo_root: Path,
    audit_enabled: bool = True,
) -> dict:
    if not can_write_events(actor):
        raise PackIngestError("forbidden", "Пакет документов доступен организатору", 403)
    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    results: list[dict] = []
    officials_count = 0
    start_entries = 0

    xlsx_files = [(n, p) for n, p in files if n.casefold().endswith(".xlsx")]
    other_files = [(n, p) for n, p in files if not n.casefold().endswith(".xlsx")]
    ordered = xlsx_files + other_files

    next_heat_no = 1
    existing_heats = list(db.scalars(select(Heat).where(Heat.event_id == event.id)).all())
    if existing_heats:
        next_heat_no = max(h.heat_number for h in existing_heats) + 1

    for filename, payload in ordered:
        if filename.casefold().endswith(".xlsx"):
            results.append(_ingest_xlsx(
                db, event=event, actor=actor, filename=filename, payload=payload,
                repo_root=repo_root, audit_enabled=audit_enabled,
            ))
            continue
        text = extract_pdf_text(payload) if filename.casefold().endswith(".pdf") else ""
        kind = _classify_pdf(filename, text)
        if kind == "start_list":
            doc = _store_document(
                db, event=event, actor=actor, filename=filename, payload=payload,
                title=Path(filename).stem.replace("_", " ")[:255],
                kind="start_list", access_class="public",
                description="IWWF start list; homologation as in file.",
                repo_root=repo_root, audit_enabled=audit_enabled,
            )
            parsed_heats = parse_startlist_text(text)
            entries = 0
            for heat in parsed_heats:
                _, added = _apply_start_heat(db, event, heat, next_heat_no)
                next_heat_no += 1
                entries += added
            start_entries += entries
            results.append({"kind": "start_list", "document_id": doc.id, "heats": len(parsed_heats), "entries": entries})
        elif kind == "official_appointment":
            doc = _store_document(
                db, event=event, actor=actor, filename=filename, payload=payload,
                title="Протокол №32-КС — судейский корпус (доска длинная/короткая)",
                kind="official_appointment", access_class="official",
                description="Утверждение судейского корпуса ЧР Казань wakesurf/wakeskim.",
                repo_root=repo_root, audit_enabled=audit_enabled,
            )
            parsed = parse_ks_protocol_text(text)
            officials_count = replace_officials(db, event_id=event.id, actor=actor, officials=parsed, commit=False)
            results.append({"kind": "officials", "document_id": doc.id, "officials": officials_count})
        else:
            doc = _store_document(
                db, event=event, actor=actor, filename=filename, payload=payload,
                title=Path(filename).stem[:255],
                kind="other", access_class="official",
                description="Загружено пакетом документов события.",
                repo_root=repo_root, audit_enabled=audit_enabled,
            )
            results.append({"kind": "document", "document_id": doc.id})

    append_audit(
        db,
        action="event.pack.ingest",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event",
        entity_id=str(event.id),
        payload={"files": [n for n, _ in files], "results": [r.get("kind") for r in results]},
        enabled=audit_enabled,
    )
    db.commit()
    return {
        "event_id": event.id,
        "files": results,
        "officials": officials_count,
        "start_entries": start_entries,
    }


async def files_from_uploads(uploads: list[UploadFile]) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    for item in uploads:
        payload = await item.read()
        out.append((item.filename or "upload.bin", payload))
    return out
