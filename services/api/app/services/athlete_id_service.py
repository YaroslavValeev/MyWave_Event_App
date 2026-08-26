"""MyWave Athlete ID — opaque permanent ID without PII."""

from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

# Crockford-like alphabet without ambiguous 0/O/1/I
_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
ATHLETE_ID_PREFIX = "MW-"
ATHLETE_ID_BODY_LEN = 8


def generate_athlete_id() -> str:
    body = "".join(secrets.choice(_ALPHABET) for _ in range(ATHLETE_ID_BODY_LEN))
    return f"{ATHLETE_ID_PREFIX}{body}"


def ensure_athlete_id(db: Session, user: User) -> str:
    """Assign athlete_id if missing; flush but do not commit."""
    if user.athlete_id:
        return user.athlete_id

    for _ in range(12):
        candidate = generate_athlete_id()
        exists = db.scalar(select(User.id).where(User.athlete_id == candidate).limit(1))
        if exists is None:
            user.athlete_id = candidate
            db.add(user)
            db.flush()
            return candidate
    raise RuntimeError("Failed to allocate unique athlete_id")


def backfill_missing_athlete_ids(db: Session) -> int:
    """Assign IDs to users that lack them. Commits."""
    users = list(db.scalars(select(User).where(User.athlete_id.is_(None))).all())
    for user in users:
        ensure_athlete_id(db, user)
    if users:
        db.commit()
    return len(users)
