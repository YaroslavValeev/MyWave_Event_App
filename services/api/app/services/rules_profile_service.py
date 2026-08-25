"""Event rules profile — create, read, update."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.rules_catalog import DISCIPLINES, default_rules_pack_for
from app.models.event_rules import EventRulesProfile
from app.models.user import User
from app.schemas.rules import EventRulesProfileCreate, EventRulesProfileOut
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, can_write_events, get_event


def _rules_packs_for_disciplines(codes: list[str]) -> dict[str, str]:
    return {code: default_rules_pack_for(code) for code in codes}


def _disciplines_label(codes: list[str]) -> str:
    titles = [DISCIPLINES[c]["title_ru"] for c in codes if c in DISCIPLINES]
    return ", ".join(titles)


def profile_to_out(profile: EventRulesProfile) -> EventRulesProfileOut:
    return EventRulesProfileOut(
        id=profile.id,
        event_id=profile.event_id,
        governing_body=profile.governing_body,
        sanction_body=profile.sanction_body,
        discipline_codes=json.loads(profile.discipline_codes_json or "[]"),
        rules_packs=json.loads(profile.rules_packs_json or "{}"),
        scoring_mode=profile.scoring_mode,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def get_rules_profile(
    db: Session,
    *,
    event_id: int,
    actor: User,
) -> EventRulesProfile | None:
    get_event(db, event_id=event_id, actor=actor)
    return db.scalar(select(EventRulesProfile).where(EventRulesProfile.event_id == event_id))


def create_rules_profile(
    db: Session,
    *,
    event_id: int,
    data: EventRulesProfileCreate,
    actor: User,
    audit_enabled: bool = True,
    commit: bool = True,
) -> EventRulesProfile:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to set rules profile", 403)

    event = get_event(db, event_id=event_id, actor=actor)
    existing = db.scalar(select(EventRulesProfile).where(EventRulesProfile.event_id == event_id))
    if existing is not None:
        raise EventServiceError("profile_exists", "Rules profile already exists for this event", 409)

    packs = _rules_packs_for_disciplines(data.discipline_codes)
    profile = EventRulesProfile(
        event_id=event.id,
        governing_body=data.governing_body,
        sanction_body=data.sanction_body,
        discipline_codes_json=json.dumps(data.discipline_codes, ensure_ascii=False),
        rules_packs_json=json.dumps(packs, ensure_ascii=False),
        scoring_mode=data.scoring_mode,
    )
    db.add(profile)
    if not event.disciplines:
        event.disciplines = _disciplines_label(data.discipline_codes)
    db.flush()

    append_audit(
        db,
        action="event_rules.create",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event_rules_profile",
        entity_id=str(profile.id),
        payload={
            "event_id": event.id,
            "governing_body": profile.governing_body,
            "sanction_body": profile.sanction_body,
            "discipline_codes": data.discipline_codes,
            "scoring_mode": profile.scoring_mode,
        },
        enabled=audit_enabled,
    )
    if commit:
        db.commit()
        db.refresh(profile)
    return profile


def upsert_rules_profile(
    db: Session,
    *,
    event_id: int,
    data: EventRulesProfileCreate,
    actor: User,
    audit_enabled: bool = True,
) -> EventRulesProfile:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to update rules profile", 403)

    event = get_event(db, event_id=event_id, actor=actor)
    profile = db.scalar(select(EventRulesProfile).where(EventRulesProfile.event_id == event_id))
    packs = _rules_packs_for_disciplines(data.discipline_codes)

    if profile is None:
        return create_rules_profile(
            db,
            event_id=event_id,
            data=data,
            actor=actor,
            audit_enabled=audit_enabled,
            commit=True,
        )

    profile.governing_body = data.governing_body
    profile.sanction_body = data.sanction_body
    profile.discipline_codes_json = json.dumps(data.discipline_codes, ensure_ascii=False)
    profile.rules_packs_json = json.dumps(packs, ensure_ascii=False)
    profile.scoring_mode = data.scoring_mode
    event.disciplines = _disciplines_label(data.discipline_codes)
    db.flush()

    append_audit(
        db,
        action="event_rules.update",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event_rules_profile",
        entity_id=str(profile.id),
        payload={
            "event_id": event.id,
            "discipline_codes": data.discipline_codes,
            "scoring_mode": profile.scoring_mode,
        },
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(profile)
    return profile
