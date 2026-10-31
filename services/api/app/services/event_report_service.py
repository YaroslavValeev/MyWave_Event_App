"""EventReport: assemble template draft from competition SoT + human publish."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.role_physical_actions import actions_for_facts
from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.models.event_report import EventReport
from app.models.heat import Heat, StartListEntry
from app.models.official import Official
from app.models.participant import Participant
from app.models.result import Result
from app.models.user import User
from app.schemas.event_report import EventReportOut, EventReportUpdate
from app.services.audit_service import append_audit
from app.services.event_report_ai import compose_ai_body
from app.services.event_service import EventServiceError, get_event
from app.services.notification_service import notify_event_staff

REPORT_EDIT_ROLES = EVENT_WRITE_ROLES | frozenset({Role.commentator})
REPORT_PUBLISH_ROLES = EVENT_WRITE_ROLES


def _role_of(user: User) -> Role:
    return Role(user.role)


def can_edit_event_report(user: User) -> bool:
    return _role_of(user) in REPORT_EDIT_ROLES


def can_publish_event_report(user: User) -> bool:
    return _role_of(user) in REPORT_PUBLISH_ROLES


def _parse_facts(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def report_to_out(row: EventReport) -> EventReportOut:
    return EventReportOut(
        id=row.id,
        event_id=row.event_id,
        status=row.status,
        title=row.title,
        body_markdown=row.body_markdown,
        facts=_parse_facts(row.facts_json),
        source=row.source,
        created_by_user_id=row.created_by_user_id,
        updated_by_user_id=row.updated_by_user_id,
        published_by_user_id=row.published_by_user_id,
        published_at=row.published_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def get_event_report(db: Session, *, event_id: int, actor: User) -> EventReport | None:
    get_event(db, event_id=event_id, actor=actor)
    row = db.scalar(select(EventReport).where(EventReport.event_id == event_id))
    if row is None:
        return None
    if row.status != "published" and not can_edit_event_report(actor):
        raise EventServiceError("forbidden", "Отчёт ещё не опубликован", 403)
    return row


def _collect_facts(db: Session, *, event_id: int) -> dict[str, Any]:
    published = list(
        db.scalars(
            select(Result)
            .where(Result.event_id == event_id, Result.status == "published")
            .order_by(Result.id.asc())
        ).all()
    )
    published.sort(key=lambda r: (r.place is None, r.place if r.place is not None else 10**9, r.id))
    participant_ids = {r.participant_id for r in published}
    dns_dnf = list(
        db.scalars(
            select(StartListEntry).where(
                StartListEntry.event_id == event_id,
                StartListEntry.status.in_(("dns", "dnf")),
            )
        ).all()
    )
    participant_ids |= {e.participant_id for e in dns_dnf}
    names: dict[int, str] = {}
    if participant_ids:
        for p in db.scalars(select(Participant).where(Participant.id.in_(participant_ids))).all():
            names[p.id] = p.full_name or f"#{p.id}"

    heats = {
        h.id: h
        for h in db.scalars(select(Heat).where(Heat.event_id == event_id)).all()
    }
    officials = [
        {"full_name": o.full_name, "position": o.position}
        for o in db.scalars(
            select(Official).where(Official.event_id == event_id).order_by(Official.sort_order)
        ).all()
    ]

    podium = [
        {
            "participant_id": r.participant_id,
            "full_name": names.get(r.participant_id, f"#{r.participant_id}"),
            "place": r.place,
            "score": r.score,
            "category_id": r.category_id,
            "heat_id": r.heat_id,
        }
        for r in published
        if r.place is not None and r.place <= 3
    ]
    results_all = [
        {
            "participant_id": r.participant_id,
            "full_name": names.get(r.participant_id, f"#{r.participant_id}"),
            "place": r.place,
            "score": r.score,
            "status": r.status,
        }
        for r in published
    ]
    exceptions = [
        {
            "participant_id": e.participant_id,
            "full_name": names.get(e.participant_id, f"#{e.participant_id}"),
            "status": e.status,
            "heat_id": e.heat_id,
            "heat_code": heats[e.heat_id].code if e.heat_id in heats else None,
        }
        for e in dns_dnf
    ]

    return {
        "assembled_at": datetime.now(UTC).isoformat(),
        "published_results_count": len(published),
        "dns_dnf_count": len(dns_dnf),
        "heats_count": len(heats),
        "podium": podium,
        "published_results": results_all,
        "dns_dnf": exceptions,
        "officials": officials,
        # Field moments layer — wire when capture module lands in runtime.
        "moments": [],
        "moments_status": "not_wired",
        "role_actions": actions_for_facts(),
    }


def _render_template_markdown(*, event_title: str, facts: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# Отчёт: {event_title}",
        "",
        f"_Собрано шаблоном {facts.get('assembled_at', '')}_",
        "",
        "## Призёры",
        "",
    ]
    podium = facts.get("podium") or []
    if not podium:
        lines.append("_Пока нет опубликованных мест 1–3._")
    else:
        for row in podium:
            place = row.get("place")
            name = row.get("full_name")
            score = row.get("score")
            score_bit = f" — {score}" if score is not None else ""
            lines.append(f"{place}. **{name}**{score_bit}")
    lines.extend(["", "## DNS / DNF", ""])
    exceptions = facts.get("dns_dnf") or []
    if not exceptions:
        lines.append("_Нет записей DNS/DNF._")
    else:
        for row in exceptions:
            heat = row.get("heat_code") or row.get("heat_id") or "—"
            lines.append(f"- {row.get('status', '?').upper()}: **{row.get('full_name')}** (heat {heat})")
    lines.extend(["", "## Судейская коллегия", ""])
    officials = facts.get("officials") or []
    if not officials:
        lines.append("_Официалы не указаны._")
    else:
        for o in officials:
            pos = o.get("position") or "официал"
            lines.append(f"- {o.get('full_name')} — {pos}")
    lines.extend(
        [
            "",
            "## Хроника дня",
            "",
            "_Добавьте 3–5 предложений: погода, ключевые заезды, инциденты._",
            "",
            "## Моменты",
            "",
            "_Фото/видео moments появятся после approve полевого захвата._",
            "",
        ]
    )
    return "\n".join(lines)


def assemble_event_report(
    db: Session,
    *,
    event_id: int,
    actor: User,
    use_llm: bool = True,
    enable_llm: bool = True,
    openai_api_key: str | None = None,
    openai_model: str = "gpt-4o-mini",
    audit_enabled: bool = True,
) -> EventReport:
    if not can_edit_event_report(actor):
        raise EventServiceError("forbidden", "Недостаточно прав для сборки отчёта", 403)

    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    row = db.scalar(select(EventReport).where(EventReport.event_id == event_id))
    if row is not None and row.status == "published":
        raise EventServiceError(
            "report_published",
            "Сначала void опубликованный отчёт, затем соберите черновик снова",
            409,
        )

    want_ai = bool(use_llm)
    if want_ai and not enable_llm:
        raise EventServiceError(
            "llm_disabled",
            "ENABLE_EVENT_REPORT_LLM выключен; передайте use_llm=false для template",
            400,
        )

    facts = _collect_facts(db, event_id=event_id)
    title = f"Отчёт — {event.title}"
    if want_ai:
        body, provider = compose_ai_body(
            event_title=event.title,
            facts=facts,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
        )
        source = "llm"
        facts["ai"] = {"provider": provider, "model": openai_model if provider == "openai" else "local"}
    else:
        body = _render_template_markdown(event_title=event.title, facts=facts)
        source = "template"
        facts["ai"] = {"provider": "none"}

    now_actor = actor.id
    facts_json = json.dumps(facts, ensure_ascii=False)

    if row is None:
        row = EventReport(
            event_id=event_id,
            status="draft",
            title=title,
            body_markdown=body,
            facts_json=facts_json,
            source=source,
            created_by_user_id=now_actor,
            updated_by_user_id=now_actor,
        )
        db.add(row)
    else:
        row.status = "draft"
        row.title = title
        row.body_markdown = body
        row.facts_json = facts_json
        row.source = source
        row.updated_by_user_id = now_actor
        row.published_at = None
        row.published_by_user_id = None

    append_audit(
        db,
        action="event_report.assemble",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event_report",
        entity_id=str(event_id),
        payload={
            "source": source,
            "ai_provider": (facts.get("ai") or {}).get("provider"),
            "published_results_count": facts.get("published_results_count"),
            "dns_dnf_count": facts.get("dns_dnf_count"),
        },
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(row)
    return row


def update_event_report(
    db: Session,
    *,
    event_id: int,
    actor: User,
    data: EventReportUpdate,
    audit_enabled: bool = True,
) -> EventReport:
    if not can_edit_event_report(actor):
        raise EventServiceError("forbidden", "Недостаточно прав для правки отчёта", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    row = db.scalar(select(EventReport).where(EventReport.event_id == event_id))
    if row is None:
        raise EventServiceError("not_found", "Отчёт не найден — сначала assemble", 404)
    if row.status == "published":
        raise EventServiceError("report_published", "Опубликованный отчёт нельзя править", 409)

    if data.title is not None:
        row.title = data.title.strip() or row.title
    if data.body_markdown is not None:
        row.body_markdown = data.body_markdown
    row.status = "draft"
    row.updated_by_user_id = actor.id

    append_audit(
        db,
        action="event_report.update",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event_report",
        entity_id=str(row.id),
        payload={"event_id": event_id},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(row)
    return row


def publish_event_report(
    db: Session,
    *,
    event_id: int,
    actor: User,
    audit_enabled: bool = True,
) -> EventReport:
    if not can_publish_event_report(actor):
        raise EventServiceError("forbidden", "Публиковать отчёт может organizer+", 403)
    event = get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    row = db.scalar(select(EventReport).where(EventReport.event_id == event_id))
    if row is None:
        raise EventServiceError("not_found", "Отчёт не найден — сначала assemble", 404)
    if row.status == "published":
        return row
    if not (row.body_markdown or "").strip():
        raise EventServiceError("empty_body", "Пустой текст отчёта", 400)

    row.status = "published"
    row.published_at = datetime.now(UTC)
    row.published_by_user_id = actor.id
    row.updated_by_user_id = actor.id

    append_audit(
        db,
        action="event_report.publish",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event_report",
        entity_id=str(row.id),
        payload={"event_id": event_id},
        enabled=audit_enabled,
    )
    notify_event_staff(
        db,
        kind="event_report.published",
        title="Отчёт о событии опубликован",
        body=f"Отчёт «{event.title}» опубликован.",
        entity_type="event",
        entity_id=str(event_id),
        exclude_user_id=actor.id,
    )
    db.commit()
    db.refresh(row)
    return row


def void_event_report(
    db: Session,
    *,
    event_id: int,
    actor: User,
    audit_enabled: bool = True,
) -> EventReport:
    if not can_publish_event_report(actor):
        raise EventServiceError("forbidden", "Void отчёта — organizer+", 403)
    get_event(db, event_id=event_id, actor=actor, require_mutable=True)
    row = db.scalar(select(EventReport).where(EventReport.event_id == event_id))
    if row is None:
        raise EventServiceError("not_found", "Отчёт не найден", 404)
    row.status = "void"
    row.updated_by_user_id = actor.id

    append_audit(
        db,
        action="event_report.void",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event_report",
        entity_id=str(row.id),
        payload={"event_id": event_id},
        enabled=audit_enabled,
    )
    db.commit()
    db.refresh(row)
    return row
