"""Result draft → verify → publish service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.heat import Heat, Run
from app.models.participant import Participant
from app.models.result import Result, ResultHistory
from app.models.user import User
from app.services.audit_service import append_audit
from app.services.event_service import EventServiceError, can_write_events, get_event

RESULT_STATUSES = frozenset({"draft", "verified", "published", "void"})


def list_results(
    db: Session,
    *,
    event_id: int,
    actor: User | None,
    status: str | None = None,
) -> list[Result]:
    get_event(db, event_id=event_id, actor=actor)
    stmt = select(Result).where(Result.event_id == event_id).order_by(Result.id)
    if status:
        stmt = stmt.where(Result.status == status)
    return list(db.scalars(stmt).all())


def upsert_draft_result(
    db: Session,
    *,
    event_id: int,
    actor: User,
    participant_id: int,
    score: float | None = None,
    place: int | None = None,
    heat_id: int | None = None,
    run_id: int | None = None,
    attempt_no: int = 1,
    notes: str | None = None,
    audit_enabled: bool = True,
) -> Result:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to manage results", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)

    part = db.get(Participant, participant_id)
    if part is None or part.event_id != event_id:
        raise EventServiceError("invalid_participant", "Participant not found for event", 400)

    if heat_id is not None:
        heat = db.get(Heat, heat_id)
        if heat is None or heat.event_id != event_id:
            raise EventServiceError("invalid_heat", "Heat not found for event", 400)

    if run_id is not None:
        run = db.get(Run, run_id)
        if run is None or run.event_id != event_id:
            raise EventServiceError("invalid_run", "Run not found for event", 400)

    existing = db.scalar(
        select(Result)
        .where(
            Result.event_id == event_id,
            Result.participant_id == participant_id,
            Result.heat_id == heat_id,
            Result.attempt_no == attempt_no,
        )
        .limit(1)
    )
    prev_status: str | None = None
    if existing is not None:
        if existing.status == "published":
            raise EventServiceError("immutable", "Published result cannot be edited; void first", 409)
        prev_status = existing.status
        existing.score = score
        existing.place = place
        existing.run_id = run_id
        existing.notes = notes
        existing.category_id = part.category_id
        if existing.status == "verified":
            existing.status = "draft"
        row = existing
    else:
        row = Result(
            event_id=event_id,
            participant_id=participant_id,
            heat_id=heat_id,
            run_id=run_id,
            category_id=part.category_id,
            attempt_no=attempt_no,
            status="draft",
            score=score,
            place=place,
            notes=notes,
            created_by_user_id=actor.id,
        )
        db.add(row)
        db.flush()

    _history(db, result=row, from_status=prev_status, to_status=row.status, actor=actor)
    append_audit(
        db,
        action="result.draft",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="result",
        entity_id=str(row.id),
        payload={"participant_id": participant_id, "score": score, "place": place},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(row)
    return row


def _history(
    db: Session,
    *,
    result: Result,
    from_status: str | None,
    to_status: str,
    actor: User,
    note: str | None = None,
) -> None:
    db.add(
        ResultHistory(
            result_id=result.id,
            event_id=result.event_id,
            from_status=from_status,
            to_status=to_status,
            score=result.score,
            place=result.place,
            actor_user_id=actor.id,
            note=note,
        )
    )


def transition_result(
    db: Session,
    *,
    event_id: int,
    result_id: int,
    actor: User,
    status: str,
    audit_enabled: bool = True,
) -> Result:
    if not can_write_events(actor):
        raise EventServiceError("forbidden", "Insufficient role to manage results", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    if status not in RESULT_STATUSES:
        raise EventServiceError("invalid_status", f"status must be one of {sorted(RESULT_STATUSES)}", 400)

    row = db.get(Result, result_id)
    if row is None or row.event_id != event_id:
        raise EventServiceError("not_found", "Result not found", 404)

    allowed = {
        "draft": {"verified", "void"},
        "verified": {"published", "draft", "void"},
        "published": {"void"},
        "void": {"draft"},
    }
    if status not in allowed.get(row.status, set()):
        raise EventServiceError(
            "invalid_transition",
            f"Cannot transition {row.status} → {status}",
            400,
        )

    prev = row.status
    row.status = status
    if status == "verified":
        row.verified_by_user_id = actor.id
    if status == "published":
        row.published_at = datetime.now(timezone.utc)

    _history(db, result=row, from_status=prev, to_status=status, actor=actor)
    append_audit(
        db,
        action=f"result.{status}",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="result",
        entity_id=str(row.id),
        payload={"from": prev, "to": status},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(row)
    return row


def list_result_history(db: Session, *, event_id: int, result_id: int, actor: User) -> list[ResultHistory]:
    get_event(db, event_id=event_id, actor=actor)
    row = db.get(Result, result_id)
    if row is None or row.event_id != event_id:
        raise EventServiceError("not_found", "Result not found", 404)
    return list(
        db.scalars(
            select(ResultHistory)
            .where(ResultHistory.result_id == result_id)
            .order_by(ResultHistory.id)
        ).all()
    )
