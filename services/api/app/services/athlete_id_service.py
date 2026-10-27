"""MyWave Athlete ID — opaque permanent ID without PII."""

from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.athlete import AccountAthleteLink, AthleteContact, AthleteProfile
from app.models.user import User

# Crockford-like alphabet without ambiguous 0/O/1/I
_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
ATHLETE_ID_PREFIX = "MW-"
ATHLETE_ID_BODY_LEN = 8


def generate_athlete_id() -> str:
    body = "".join(secrets.choice(_ALPHABET) for _ in range(ATHLETE_ID_BODY_LEN))
    return f"{ATHLETE_ID_PREFIX}{body}"


def allocate_athlete_id(db: Session) -> str:
    for _ in range(16):
        candidate = generate_athlete_id()
        on_user = db.scalar(select(User.id).where(User.athlete_id == candidate).limit(1))
        on_profile = db.scalar(
            select(AthleteProfile.id).where(AthleteProfile.athlete_id == candidate).limit(1)
        )
        if on_user is None and on_profile is None:
            return candidate
    raise RuntimeError("Failed to allocate unique athlete_id")


def ensure_athlete_id(db: Session, user: User) -> str:
    """Assign athlete_id if missing; create organic self-profile when user has no links."""
    if not user.athlete_id:
        user.athlete_id = allocate_athlete_id(db)
        db.add(user)
        db.flush()

    has_link = db.scalar(
        select(AccountAthleteLink.id).where(AccountAthleteLink.user_id == user.id).limit(1)
    )
    if has_link is None:
        profile = db.scalar(
            select(AthleteProfile).where(AthleteProfile.athlete_id == user.athlete_id)
        )
        if profile is None:
            profile = AthleteProfile(
                athlete_id=user.athlete_id,
                display_name=user.display_name or user.email,
            )
            db.add(profile)
            db.flush()
            if user.phone:
                db.add(
                    AthleteContact(
                        athlete_profile_id=profile.id,
                        phone_e164=user.phone,
                        kind="self",
                    )
                )
            db.add(
                AccountAthleteLink(
                    user_id=user.id,
                    athlete_profile_id=profile.id,
                    relation="self",
                    status="confirmed",
                )
            )
            db.flush()
    return user.athlete_id


def backfill_missing_athlete_ids(db: Session) -> int:
    """Assign IDs to users that lack them. Commits."""
    users = list(db.scalars(select(User).where(User.athlete_id.is_(None))).all())
    for user in users:
        ensure_athlete_id(db, user)
    if users:
        db.commit()
    return len(users)


def canonical_athlete_id(db: Session, user: User) -> str | None:
    """Prefer confirmed self-profile ID; otherwise the account-level ID."""
    link = db.scalar(
        select(AccountAthleteLink)
        .where(
            AccountAthleteLink.user_id == user.id,
            AccountAthleteLink.relation == "self",
            AccountAthleteLink.status == "confirmed",
        )
        .limit(1)
    )
    if link:
        profile = db.get(AthleteProfile, link.athlete_profile_id)
        if profile:
            return profile.athlete_id
    return user.athlete_id
