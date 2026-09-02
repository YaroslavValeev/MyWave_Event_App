"""Apply transcribed Kazan scan sheets into heats / start lists / draft results."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.data.kazan_2026_protocol import FVLS_EVENT_BLURB, HEATS, ROUND_TITLE
from app.models.athlete import AthleteProfile
from app.models.category import Category
from app.models.event import Event
from app.models.heat import Heat, Run, StartListEntry
from app.models.official import Official
from app.models.participant import Participant
from app.models.result import Result, ResultHistory
from app.models.user import User
from app.services.athlete_id_service import allocate_athlete_id
from app.services.audit_service import append_audit
from app.services.category_canon import category_title
from app.services.event_pack_service import _get_or_create_canon_category, _latin_key
from app.services.event_service import EventServiceError, can_write_events, get_event
from app.services.heat_service import clear_start_list


def _match_or_create_participant(
    db: Session, event: Event, category: Category, latin: str, ru: str | None = None
) -> Participant:
    want = _latin_key(latin)
    same_cat = list(
        db.scalars(
            select(Participant).where(
                Participant.event_id == event.id,
                Participant.category_id == category.id,
            )
        ).all()
    )
    for part in same_cat:
        profile = db.get(AthleteProfile, part.athlete_profile_id) if part.athlete_profile_id else None
        names = [part.full_name, profile.latin_name if profile else None, profile.display_name if profile else None]
        if any(_latin_key(n) == want for n in names if n):
            if ru:
                part.full_name = ru
                db.add(part)
                if profile and (not profile.display_name or profile.display_name == latin):
                    profile.display_name = ru
                    db.add(profile)
            return part

    profile: AthleteProfile | None = None
    all_parts = list(db.scalars(select(Participant).where(Participant.event_id == event.id)).all())
    for part in all_parts:
        cand = db.get(AthleteProfile, part.athlete_profile_id) if part.athlete_profile_id else None
        names = [part.full_name, cand.latin_name if cand else None, cand.display_name if cand else None]
        if any(_latin_key(n) == want for n in names if n):
            profile = cand
            break
    display = ru or latin
    if profile is None:
        profile = AthleteProfile(athlete_id=allocate_athlete_id(db), display_name=display, latin_name=latin)
        db.add(profile)
        db.flush()
    else:
        if not profile.latin_name:
            profile.latin_name = latin
        if ru and (not profile.display_name or profile.display_name == latin):
            profile.display_name = ru
        db.add(profile)

    part = Participant(
        event_id=event.id,
        category_id=category.id,
        athlete_profile_id=profile.id,
        full_name=display,
        status="registered",
    )
    db.add(part)
    db.flush()
    return part


def _upsert_heat(db: Session, event: Event, spec: dict, category: Category, heat_number: int) -> Heat:
    scheduled = datetime.fromisoformat(spec["scheduled_at"])
    round_ru = ROUND_TITLE.get(spec["round"], spec["round"])
    title = f"{category_title(spec['iwwf_class'], spec['sex'])} · {round_ru}"
    if spec["heat_index"] > 1:
        title += f" · заезд {spec['heat_index']}"
    src = spec.get("source") or "owner_scan"
    notes = (
        f"source={src}; homologation=not_homologated; engine={spec['engine']}; "
        f"chief={spec.get('chief_judge') or ''}; scorer={spec.get('scorer') or ''}"
    )
    if spec.get("time_inferred"):
        notes += "; time_inferred"
    heat = db.scalar(select(Heat).where(Heat.event_id == event.id, Heat.code == spec["code"]))
    done = any(
        e.get("score") is not None or e.get("dns") or e.get("place") is not None for e in spec["entries"]
    )
    status = "completed" if done else "planned"
    if heat is None:
        heat = Heat(
            event_id=event.id,
            code=spec["code"][:64],
            title=title[:255],
            heat_number=heat_number,
            category_id=category.id,
            scheduled_at=scheduled,
            status=status,
            notes=notes,
        )
        db.add(heat)
        db.flush()
        return heat
    heat.title = title[:255]
    heat.category_id = category.id
    heat.scheduled_at = scheduled
    heat.status = status
    heat.notes = notes
    db.flush()
    return heat


def _ensure_official(db: Session, event: Event, full_name: str, position: str, sort_order: int) -> None:
    found = db.scalar(
        select(Official).where(Official.event_id == event.id, Official.full_name == full_name)
    )
    if found:
        return
    db.add(
        Official(
            event_id=event.id,
            sort_order=sort_order,
            full_name=full_name,
            position=position,
            notes="Со скана протокола заезда (вейкборд-катер). Не заменяет судей 32-КС.",
        )
    )


def apply_scan_protocol(
    db: Session,
    *,
    event_id: int,
    actor: User,
    heats: list[dict] | None = None,
    audit_enabled: bool = True,
    commit: bool = True,
) -> dict:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Недостаточно прав", 403)
    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    pack = heats if heats is not None else HEATS
    if pack is HEATS:
        if not (event.venue or "").strip():
            event.venue = "оз. Нижний Кабан"
        if not (event.location or "").strip():
            event.location = "оз. Нижний Кабан, Казань"
        if not (event.description or "").strip():
            event.description = FVLS_EVENT_BLURB
        db.add(event)
    _ensure_official(db, event, "Balakin Alexandr", "Главный судья (вейкборд-катер)", 12)
    existing = list(db.scalars(select(Heat).where(Heat.event_id == event.id)).all())
    next_no = max((h.heat_number for h in existing), default=0) + 1
    heat_count = 0
    entry_count = 0
    result_count = 0
    dns_count = 0
    for spec in pack:
        category = _get_or_create_canon_category(
            db,
            event,
            discipline=spec["discipline"],
            label=f"{spec['iwwf_class']} {spec['sex']}",
            sex_hint=spec["sex"],
        )
        heat = _upsert_heat(db, event, spec, category, next_no)
        if heat.heat_number >= next_no:
            next_no = heat.heat_number + 1
        heat_count += 1
        db.execute(update(Result).where(Result.heat_id == heat.id).values(run_id=None))
        clear_start_list(db, heat_id=heat.id)
        for row in spec["entries"]:
            part = _match_or_create_participant(db, event, category, row["latin"], ru=row.get("ru"))
            if row.get("dns"):
                status = "dns"
            elif row.get("score") is not None or row.get("place") is not None:
                status = "completed"
            else:
                status = "scheduled"
            note_bits = [row["latin"]]
            if row.get("seeded"):
                note_bits.append("seeded")
            if row.get("q"):
                note_bits.append(f"Q={row['q']}")
            entry = StartListEntry(
                heat_id=heat.id,
                event_id=event.id,
                participant_id=part.id,
                start_order=int(row["order"]),
                status=status,
                notes="; ".join(note_bits),
            )
            db.add(entry)
            db.flush()
            run = Run(
                event_id=event.id,
                heat_id=heat.id,
                start_list_entry_id=entry.id,
                participant_id=part.id,
                attempt_no=1,
                status=status,
            )
            db.add(run)
            db.flush()
            entry_count += 1
            if row.get("dns"):
                dns_count += 1
            if row.get("score") is not None or row.get("place") is not None or row.get("dns"):
                criteria = row.get("criteria") or {}
                notes = json.dumps(
                    {
                        "source": spec.get("source") or "owner_scan",
                        "homologation": "not_homologated",
                        "q": row.get("q"),
                        "dns": bool(row.get("dns")),
                        "criteria": criteria,
                        "engine": spec["engine"],
                        "ru": row.get("ru"),
                    },
                    ensure_ascii=False,
                )
                existing_res = db.scalar(
                    select(Result).where(
                        Result.event_id == event.id,
                        Result.participant_id == part.id,
                        Result.heat_id == heat.id,
                        Result.attempt_no == 1,
                    )
                )
                if existing_res and existing_res.status == "published":
                    continue
                if existing_res:
                    existing_res.score = row.get("score")
                    existing_res.place = row.get("place")
                    existing_res.run_id = run.id
                    existing_res.notes = notes
                    existing_res.status = "draft"
                    db.add(existing_res)
                else:
                    res = Result(
                        event_id=event.id,
                        participant_id=part.id,
                        heat_id=heat.id,
                        run_id=run.id,
                        category_id=part.category_id,
                        attempt_no=1,
                        status="draft",
                        score=row.get("score"),
                        place=row.get("place"),
                        notes=notes,
                        created_by_user_id=actor.id,
                    )
                    db.add(res)
                    db.flush()
                    db.add(
                        ResultHistory(
                            result_id=res.id,
                            event_id=event.id,
                            from_status=None,
                            to_status="draft",
                            score=res.score,
                            place=res.place,
                            actor_user_id=actor.id,
                            note="scan ingest",
                        )
                    )
                result_count += 1
        db.flush()

    append_audit(
        db,
        action="event.scan_protocol.ingest",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event",
        entity_id=str(event.id),
        payload={"heats": heat_count, "entries": entry_count, "results": result_count},
        enabled=audit_enabled,
    )
    if commit:
        db.commit()
    return {
        "event_id": event.id,
        "heats": heat_count,
        "entries": entry_count,
        "results": result_count,
        "dns": dns_count,
    }
