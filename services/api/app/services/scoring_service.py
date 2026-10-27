"""Structured judge scoring → panel aggregate → result draft."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.roles import JUDGE_SCORE_ROLES, RESULT_VERIFY_ROLES, Role
from app.domain.scoring_engines import (
    ScoringError,
    aggregate_panel,
    engine_meta,
    judge_sheet_total,
    normalize_criteria_scores,
)
from app.domain.rules_catalog import RULES_PACKS, default_rules_pack_for
from app.models.judge_score import JudgeScore
from app.models.participant import Participant
from app.models.user import User
from app.schemas.scoring import JudgeScoreSubmit
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, get_event
from app.services.result_service import upsert_draft_result
from app.services.rules_profile_service import get_rules_profile


def _role(user: User) -> Role:
    return Role(user.role)


def can_submit_judge_score(user: User) -> bool:
    return _role(user) in JUDGE_SCORE_ROLES


def resolve_engine_for_event(db: Session, *, event_id: int, actor: User) -> str:
    profile = get_rules_profile(db, event_id=event_id, actor=actor)
    if profile is None:
        return "MANUAL_PLACE"
    packs = json.loads(profile.rules_packs_json or "{}")
    codes = json.loads(profile.discipline_codes_json or "[]")
    if not codes:
        return "MANUAL_PLACE"
    # Primary discipline = first selected
    pack_id = packs.get(codes[0]) or default_rules_pack_for(codes[0])
    meta = RULES_PACKS.get(pack_id) or {}
    return str(meta.get("engine") or "MANUAL_PLACE")


def list_judge_scores(
    db: Session,
    *,
    event_id: int,
    actor: User,
    participant_id: int | None = None,
    heat_id: int | None = None,
) -> list[JudgeScore]:
    get_event(db, event_id=event_id, actor=actor)
    stmt = select(JudgeScore).where(JudgeScore.event_id == event_id)
    if participant_id is not None:
        stmt = stmt.where(JudgeScore.participant_id == participant_id)
    if heat_id is not None:
        stmt = stmt.where(JudgeScore.heat_id == heat_id)
    return list(db.scalars(stmt.order_by(JudgeScore.id.desc())).all())


def submit_judge_score(
    db: Session,
    *,
    event_id: int,
    actor: User,
    data: JudgeScoreSubmit,
    audit_enabled: bool = True,
) -> JudgeScore:
    if not can_submit_judge_score(actor):
        raise EventServiceError("forbidden", "Insufficient role to submit judge scores", 403)

    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    part = db.get(Participant, data.participant_id)
    if part is None or part.event_id != event_id:
        raise EventServiceError("invalid_participant", "Participant not found for event", 400)

    engine = data.engine or resolve_engine_for_event(db, event_id=event_id, actor=actor)
    if engine == "MANUAL_PLACE":
        raise EventServiceError(
            "engine_manual",
            "Event uses manual/photo protocol mode — use Results or ProtocolCapture",
            400,
        )

    try:
        criteria_norm = normalize_criteria_scores(engine, data.criteria)
        total = judge_sheet_total(engine, criteria_norm)
    except ScoringError as exc:
        raise EventServiceError(exc.code, exc.message, 400) from exc

    existing = db.scalar(
        select(JudgeScore).where(
            JudgeScore.event_id == event_id,
            JudgeScore.participant_id == data.participant_id,
            JudgeScore.judge_user_id == actor.id,
            JudgeScore.attempt_no == data.attempt_no,
        )
    )
    if existing is not None:
        existing.engine = engine
        existing.heat_id = data.heat_id
        existing.criteria_json = json.dumps(criteria_norm, ensure_ascii=False)
        existing.total = total
        existing.notes = data.notes
        row = existing
    else:
        row = JudgeScore(
            event_id=event_id,
            participant_id=data.participant_id,
            heat_id=data.heat_id,
            judge_user_id=actor.id,
            attempt_no=data.attempt_no,
            engine=engine,
            criteria_json=json.dumps(criteria_norm, ensure_ascii=False),
            total=total,
            notes=data.notes,
        )
        db.add(row)
    db.flush()

    append_audit(
        db,
        action="judge_score.submit",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="judge_score",
        entity_id=str(row.id),
        payload={
            "participant_id": data.participant_id,
            "engine": engine,
            "total": total,
            "attempt_no": data.attempt_no,
        },
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(row)
    return row


def aggregate_to_result(
    db: Session,
    *,
    event_id: int,
    actor: User,
    participant_id: int,
    heat_id: int | None = None,
    attempt_no: int = 1,
    write_result_draft: bool = True,
    place: int | None = None,
    audit_enabled: bool = True,
) -> dict:
    if Role(actor.role) not in RESULT_VERIFY_ROLES:
        raise EventServiceError("forbidden", "Only organizer/chief judge can aggregate panel scores", 403)

    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    sheets = list(
        db.scalars(
            select(JudgeScore).where(
                JudgeScore.event_id == event_id,
                JudgeScore.participant_id == participant_id,
                JudgeScore.attempt_no == attempt_no,
            )
        ).all()
    )
    if heat_id is not None:
        sheets = [s for s in sheets if s.heat_id == heat_id]
    if not sheets:
        raise EventServiceError("no_scores", "No judge scores for this participant/attempt", 400)

    engine = sheets[0].engine
    try:
        panel = aggregate_panel(
            engine,
            [s.total for s in sheets],
            drop_extremes=(engine == "WSWS_DRIVE" and len(sheets) >= 5),
        )
    except ScoringError as exc:
        raise EventServiceError(exc.code, exc.message, 400) from exc

    result_id = None
    if write_result_draft:
        result = upsert_draft_result(
            db,
            event_id=event_id,
            actor=actor,
            participant_id=participant_id,
            score=panel["panel_score"],
            place=place,
            heat_id=heat_id,
            attempt_no=attempt_no,
            notes=f"panel:{engine}; judges={panel['judge_count']}",
            audit_enabled=audit_enabled,
        )
        result_id = result.id

    append_audit(
        db,
        action="judge_score.aggregate",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="result" if result_id else "event",
        entity_id=str(result_id or event_id),
        payload={"participant_id": participant_id, **panel},
        enabled=audit_enabled,
    )
    db.commit()

    return {**panel, "result_id": result_id, "detail": panel}


def score_out(row: JudgeScore) -> dict:
    try:
        criteria = json.loads(row.criteria_json or "{}")
    except json.JSONDecodeError:
        criteria = {}
    return {
        "id": row.id,
        "event_id": row.event_id,
        "participant_id": row.participant_id,
        "heat_id": row.heat_id,
        "judge_user_id": row.judge_user_id,
        "attempt_no": row.attempt_no,
        "engine": row.engine,
        "criteria": criteria,
        "total": row.total,
        "notes": row.notes,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
