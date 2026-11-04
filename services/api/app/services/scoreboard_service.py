"""Live scoreboard projection over Result SoT (ADR-0016)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.models.heat import StartListEntry
from app.models.participant import Participant
from app.models.result import Result
from app.models.user import User
from app.services.event_service import get_event


def _can_see_unofficial(actor: User | None) -> bool:
    if actor is None:
        return False
    try:
        return Role(actor.role) in EVENT_WRITE_ROLES or Role(actor.role) == Role.judge
    except ValueError:
        return False


def build_scoreboard(
    db: Session,
    *,
    event_id: int,
    actor: User | None,
    include_unofficial: bool = False,
) -> dict[str, Any]:
    get_event(db, event_id=event_id, actor=actor)
    show_unofficial = include_unofficial and _can_see_unofficial(actor)

    statuses = ("published",) if not show_unofficial else ("published", "verified", "draft")
    rows = list(
        db.scalars(
            select(Result)
            .where(Result.event_id == event_id, Result.status.in_(statuses))
            .order_by(
                Result.place.is_(None),
                Result.place.asc(),
                Result.score.desc(),
                Result.id.asc(),
            )
        ).all()
    )

    # Latest DNS/DNF flags from start lists (no second scoring SoT).
    dns_dnf: dict[int, str] = {}
    for sle in db.scalars(
        select(StartListEntry).where(
            StartListEntry.event_id == event_id,
            StartListEntry.status.in_(("dns", "dnf")),
        )
    ).all():
        dns_dnf[sle.participant_id] = sle.status.upper()

    participant_ids = {r.participant_id for r in rows if r.participant_id} | set(dns_dnf)
    names: dict[int, str] = {}
    if participant_ids:
        for p in db.scalars(select(Participant).where(Participant.id.in_(participant_ids))).all():
            names[p.id] = p.full_name or p.name_latin or f"#{p.id}"

    entries: list[dict[str, Any]] = []
    for r in rows:
        flag = dns_dnf.get(r.participant_id or -1)
        entries.append(
            {
                "result_id": r.id,
                "participant_id": r.participant_id,
                "display_name": names.get(r.participant_id or -1, "—"),
                "status": r.status,
                "score": r.score,
                "place": r.place,
                "category_id": r.category_id,
                "updated_at": r.updated_at.isoformat() if isinstance(r.updated_at, datetime) else None,
                "official": r.status == "published",
                "run_flag": flag,
            }
        )

    # Also surface DNS/DNF without a Result row (spectator sees no-shows).
    result_pids = {e["participant_id"] for e in entries}
    for pid, flag in dns_dnf.items():
        if pid in result_pids:
            continue
        entries.append(
            {
                "result_id": -pid,
                "participant_id": pid,
                "display_name": names.get(pid) or _participant_name(db, pid),
                "status": flag.lower(),
                "score": None,
                "place": None,
                "category_id": None,
                "updated_at": None,
                "official": False,
                "run_flag": flag,
            }
        )

    fingerprint = hashlib.sha256(
        json.dumps(
            [
                {
                    "id": e["result_id"],
                    "s": e["status"],
                    "sc": e["score"],
                    "p": e["place"],
                    "f": e.get("run_flag"),
                }
                for e in entries
            ],
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()[:16]

    return {
        "event_id": event_id,
        "revision": fingerprint,
        "include_unofficial": show_unofficial,
        "entries": entries,
        "total": len(entries),
    }


def _participant_name(db: Session, participant_id: int) -> str:
    p = db.get(Participant, participant_id)
    if p is None:
        return f"#{participant_id}"
    return p.full_name or p.name_latin or f"#{participant_id}"
