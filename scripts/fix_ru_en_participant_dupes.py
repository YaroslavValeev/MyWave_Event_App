"""Find and merge Cyrillic/Latin duplicate participant rows on one event.

Keeps the Cyrillic (or richer) row as primary, moves Latin spelling into
name_latin, re-points start_list / scores / results, then deletes the twin.

Usage (API container or local with DATABASE_URL):
  python scripts/fix_ru_en_participant_dupes.py --event-slug chr-pr-kazan-2026 --apply
  python scripts/fix_ru_en_participant_dupes.py --event-id 1 --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "services" / "api"
sys.path.insert(0, str(API_DIR))

from sqlalchemy import select, update  # noqa: E402

from app.db import get_session_factory, init_db  # noqa: E402
from app.models import Category, Event, Participant  # noqa: E402
from app.models.heat import Run, StartListEntry  # noqa: E402
from app.models.judge_score import JudgeScore  # noqa: E402
from app.models.result import Result  # noqa: E402

_CYR = re.compile(r"[А-Яа-яЁё]")
_LAT = re.compile(r"[A-Za-z]")


def _cyr(s: str | None) -> bool:
    return bool(s and _CYR.search(s))


def _lat_only(s: str | None) -> bool:
    return bool(s and _LAT.search(s) and not _CYR.search(s))


def _token_key(name: str) -> str:
    parts = [p for p in re.split(r"[\s.]+", name.strip().casefold()) if p]
    return " ".join(parts[:2]) if parts else name.casefold()


def _same_person(a: Participant, b: Participant) -> bool:
    if a.event_id != b.event_id:
        return False
    if a.phone and b.phone and a.phone == b.phone:
        return True
    if (
        a.birth_year
        and b.birth_year
        and a.birth_year == b.birth_year
        and a.category_id
        and a.category_id == b.category_id
    ):
        return True
    if a.birth_year and b.birth_year and a.birth_year == b.birth_year:
        # Same discipline via category lookup is done by caller grouping.
        return _token_key(a.full_name) == _token_key(b.full_name)
    return False


def _pick_keeper(a: Participant, b: Participant) -> tuple[Participant, Participant]:
    """Return (keep, drop). Prefer Cyrillic full_name."""
    a_c, b_c = _cyr(a.full_name), _cyr(b.full_name)
    if a_c and not b_c:
        return a, b
    if b_c and not a_c:
        return b, a
    if (a.name_latin or "") and not (b.name_latin or ""):
        return a, b
    if (b.name_latin or "") and not (a.name_latin or ""):
        return b, a
    return (a, b) if a.id <= b.id else (b, a)


def _repoint(db, keep_id: int, drop_id: int) -> None:
    # Start list: unique (heat_id, participant_id) — drop twin row if keep already on heat.
    drop_entries = db.scalars(
        select(StartListEntry).where(StartListEntry.participant_id == drop_id)
    ).all()
    for entry in drop_entries:
        exists = db.scalar(
            select(StartListEntry.id).where(
                StartListEntry.heat_id == entry.heat_id,
                StartListEntry.participant_id == keep_id,
            )
        )
        if exists:
            db.delete(entry)
        else:
            entry.participant_id = keep_id

    for model in (Run, JudgeScore, Result):
        db.execute(
            update(model)
            .where(model.participant_id == drop_id)
            .values(participant_id=keep_id)
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-id", type=int, default=None)
    parser.add_argument("--event-slug", type=str, default="chr-pr-kazan-2026")
    parser.add_argument("--apply", action="store_true", help="Write merges (default dry-run)")
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()
    apply = bool(args.apply)

    init_db()
    db = get_session_factory()()
    try:
        event = None
        if args.event_id:
            event = db.get(Event, args.event_id)
        if event is None:
            event = db.scalar(select(Event).where(Event.slug == args.event_slug))
        if event is None:
            raise SystemExit("Event not found")

        parts = list(
            db.scalars(select(Participant).where(Participant.event_id == event.id)).all()
        )
        cats = {
            c.id: c
            for c in db.scalars(select(Category).where(Category.event_id == event.id)).all()
        }

        # Report latin-only primaries (likely missing Cyrillic companion field)
        latin_primaries = [p for p in parts if _lat_only(p.full_name)]
        print(f"event_id={event.id} participants={len(parts)} latin_as_full_name={len(latin_primaries)}")

        pairs: list[tuple[Participant, Participant]] = []
        used: set[int] = set()
        for i, a in enumerate(parts):
            if a.id in used:
                continue
            for b in parts[i + 1 :]:
                if b.id in used:
                    continue
                ca, cb = cats.get(a.category_id), cats.get(b.category_id)
                same_disc = (
                    ca
                    and cb
                    and (ca.discipline or "") == (cb.discipline or "")
                    and (ca.title or "") == (cb.title or "")
                )
                mixed_script = (_cyr(a.full_name) and _lat_only(b.full_name)) or (
                    _cyr(b.full_name) and _lat_only(a.full_name)
                )
                if not mixed_script:
                    continue
                if not (_same_person(a, b) or same_disc and a.birth_year == b.birth_year):
                    continue
                pairs.append((a, b))
                used.add(a.id)
                used.add(b.id)
                break

        print(f"candidate_ru_en_pairs={len(pairs)}")
        merged = 0
        for a, b in pairs:
            keep, drop = _pick_keeper(a, b)
            latin = drop.full_name if _lat_only(drop.full_name) else drop.name_latin
            if keep.name_latin and latin and keep.name_latin.casefold() != latin.casefold():
                latin = f"{keep.name_latin} / {latin}"
            print(
                f"  MERGE keep=#{keep.id} {keep.full_name!r} "
                f"<- drop=#{drop.id} {drop.full_name!r} name_latin={latin!r}"
            )
            if apply:
                if latin and not keep.name_latin:
                    keep.name_latin = latin
                elif latin and keep.name_latin and latin.casefold() not in keep.name_latin.casefold():
                    keep.name_latin = f"{keep.name_latin} / {latin}"
                if drop.phone and not keep.phone:
                    keep.phone = drop.phone
                if drop.has_medical_cert and not keep.has_medical_cert:
                    keep.has_medical_cert = True
                    keep.medical_cert_url = drop.medical_cert_url
                _repoint(db, keep.id, drop.id)
                db.delete(drop)
                merged += 1

        if apply:
            db.commit()
            print(f"APPLIED merges={merged}")
        else:
            print("DRY-RUN (pass --apply to write)")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
