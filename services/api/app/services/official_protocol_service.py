"""Official protocol JSON/HTML export bundle."""

from __future__ import annotations

import html
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import __version__
from app.models.judge_score import JudgeScore
from app.models.protocol_capture import ProtocolCapture
from app.models.result import Result
from app.models.user import User
from app.schemas.official_protocol import OfficialProtocolBundle, OfficialProtocolReadiness
from app.services.audit_service import append_audit
from app.services.competition_service import list_categories, list_officials, list_participants
from app.services.event_service import EventServiceError, can_write_events, get_event
from app.services.heat_service import list_heats, list_start_list
from app.services.rules_profile_service import get_rules_profile, profile_to_out
from app.services.scoring_service import resolve_engine_for_event, score_out


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _assess_readiness(
    *,
    rules_profile: dict[str, Any] | None,
    published_results: int,
    published_captures: int,
) -> OfficialProtocolReadiness:
    warnings: list[str] = []
    blockers: list[str] = []

    if rules_profile is None:
        blockers.append("rules_profile_missing")
    elif rules_profile.get("governing_body") == "FVLS" and rules_profile.get("sanction_body") != "IWWF":
        warnings.append("fvls_requires_iwwf_sanction_for_official_protocol")

    if published_results == 0 and published_captures == 0:
        blockers.append("no_published_results_or_protocol_captures")

    official_ready = len(blockers) == 0
    return OfficialProtocolReadiness(
        official_ready=official_ready,
        warnings=warnings,
        blockers=blockers,
        published_results_count=published_results,
        published_protocol_captures_count=published_captures,
    )


def build_official_protocol_bundle(
    db: Session,
    *,
    event_id: int,
    actor: User,
) -> OfficialProtocolBundle:
    if not can_write_events(actor):
        raise EventServiceError(
            "forbidden",
            "Insufficient role to export official protocol",
            403,
        )

    event = get_event(db, event_id=event_id, actor=actor)
    profile_row = get_rules_profile(db, event_id=event_id, actor=actor)
    rules_profile = profile_to_out(profile_row).model_dump(mode="json") if profile_row else None

    try:
        scoring_engine = resolve_engine_for_event(db, event_id=event_id, actor=actor)
    except EventServiceError:
        scoring_engine = None

    officials = [
        {
            "id": o.id,
            "full_name": o.full_name,
            "position": o.position,
            "region": o.region,
            "judge_category": o.judge_category,
            "sort_order": o.sort_order,
        }
        for o in list_officials(db, event_id=event_id, actor=actor)
    ]

    categories = [
        {
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "discipline": c.discipline,
        }
        for c in list_categories(db, event_id=event_id, actor=actor)
    ]

    participants = [
        {
            "id": p.id,
            "category_id": p.category_id,
            "user_id": p.user_id,
            "athlete_id": None,
            "full_name": p.full_name,
            "club": p.club,
            "region": p.region,
            "city": p.city,
            "gender": p.gender,
            "birth_year": p.birth_year,
            "status": p.status,
        }
        for p in list_participants(db, event_id=event_id, actor=actor)
    ]
    user_ids = {p["user_id"] for p in participants if p.get("user_id")}
    if user_ids:
        for row in db.scalars(select(User).where(User.id.in_(user_ids))).all():
            for item in participants:
                if item.get("user_id") == row.id:
                    item["athlete_id"] = row.athlete_id

    heats_out: list[dict[str, Any]] = []
    for heat in list_heats(db, event_id=event_id, actor=actor):
        entries = list_start_list(db, event_id=event_id, heat_id=heat.id, actor=actor)
        heats_out.append(
            {
                "id": heat.id,
                "code": heat.code,
                "title": heat.title,
                "heat_number": heat.heat_number,
                "category_id": heat.category_id,
                "status": heat.status,
                "scheduled_at": _iso(heat.scheduled_at),
                "start_list": [
                    {
                        "id": e.id,
                        "participant_id": e.participant_id,
                        "start_order": e.start_order,
                        "status": e.status,
                    }
                    for e in entries
                ],
            }
        )

    all_results = list(
        db.scalars(select(Result).where(Result.event_id == event_id).order_by(Result.id)).all()
    )
    published_results = [r for r in all_results if r.status == "published"]
    results_out = [
        {
            "id": r.id,
            "participant_id": r.participant_id,
            "category_id": r.category_id,
            "heat_id": r.heat_id,
            "run_id": r.run_id,
            "attempt_no": r.attempt_no,
            "status": r.status,
            "score": r.score,
            "place": r.place,
            "notes": r.notes,
            "published_at": _iso(r.published_at),
        }
        for r in all_results
    ]

    captures = list(
        db.scalars(
            select(ProtocolCapture)
            .where(ProtocolCapture.event_id == event_id)
            .order_by(ProtocolCapture.id)
        ).all()
    )
    published_captures = [c for c in captures if c.status == "published"]
    protocol_out: list[dict[str, Any]] = []
    for capture in captures:
        extracted = None
        if capture.extracted_json:
            try:
                extracted = json.loads(capture.extracted_json)
            except json.JSONDecodeError:
                extracted = None
        protocol_out.append(
            {
                "id": capture.id,
                "heat_id": capture.heat_id,
                "title": capture.title,
                "kind": capture.kind,
                "status": capture.status,
                "file_name": capture.file_name,
                "mime_type": capture.mime_type,
                "notes": capture.notes,
                "extracted": extracted,
                "verified_at": _iso(capture.verified_at),
            }
        )

    judge_rows = list(
        db.scalars(
            select(JudgeScore).where(JudgeScore.event_id == event_id).order_by(JudgeScore.id)
        ).all()
    )
    judge_scores = [score_out(row) for row in judge_rows]
    for item in judge_scores:
        item["created_at"] = _iso(item.get("created_at"))
        item["updated_at"] = _iso(item.get("updated_at"))

    readiness = _assess_readiness(
        rules_profile=rules_profile,
        published_results=len(published_results),
        published_captures=len(published_captures),
    )

    return OfficialProtocolBundle(
        generated_at=datetime.now(UTC),
        generator=f"MyWave Event App API {__version__}",
        event={
            "id": event.id,
            "slug": event.slug,
            "title": event.title,
            "description": event.description,
            "city": event.city,
            "location": event.location,
            "venue": event.venue,
            "disciplines": event.disciplines,
            "starts_at": _iso(event.starts_at),
            "ends_at": _iso(event.ends_at),
            "status": event.status,
        },
        rules_profile=rules_profile,
        scoring_engine=scoring_engine,
        officials=officials,
        categories=categories,
        participants=participants,
        heats=heats_out,
        results=results_out,
        protocol_captures=protocol_out,
        judge_scores=judge_scores,
        readiness=readiness,
    )


def record_official_protocol_export(
    db: Session,
    *,
    event_id: int,
    actor: User,
    export_format: str,
    audit_enabled: bool = True,
) -> None:
    append_audit(
        db,
        action="official_protocol.export",
        actor_user_id=actor.id,
        actor_email=actor.email,
        entity_type="event",
        entity_id=str(event_id),
        payload={"format": export_format},
        enabled=audit_enabled,
    )
    db.commit()


def render_official_protocol_html(bundle: OfficialProtocolBundle) -> str:
    event = bundle.event
    title = html.escape(str(event.get("title") or "Событие"))
    slug = html.escape(str(event.get("slug") or ""))
    venue = html.escape(
        ", ".join(
            x
            for x in [event.get("city"), event.get("venue"), event.get("location")]
            if x
        )
        or "—"
    )
    disciplines = html.escape(str(event.get("disciplines") or "—"))
    status = html.escape(str(event.get("status") or ""))

    profile = bundle.rules_profile or {}
    gov = html.escape(str(profile.get("governing_body") or "—"))
    sanction = html.escape(str(profile.get("sanction_body") or "—"))
    scoring_mode = html.escape(str(profile.get("scoring_mode") or "—"))
    engine = html.escape(str(bundle.scoring_engine or "—"))

    officials_rows = "".join(
        f"<tr><td>{html.escape(o['full_name'])}</td>"
        f"<td>{html.escape(o['position'])}</td>"
        f"<td>{html.escape(o.get('region') or '—')}</td></tr>"
        for o in bundle.officials
    ) or "<tr><td colspan='3'>—</td></tr>"

    published = [r for r in bundle.results if r.get("status") == "published"]
    part_map = {p["id"]: p["full_name"] for p in bundle.participants}
    result_lines: list[str] = []
    for r in sorted(published, key=lambda x: (x.get("place") or 9999, x.get("id") or 0)):
        pid = r["participant_id"]
        name = html.escape(part_map.get(pid, f"#{pid}"))
        score = r.get("score") if r.get("score") is not None else "—"
        result_lines.append(
            f"<tr><td>{r.get('place') or '—'}</td>"
            f"<td>{name}</td>"
            f"<td>{score}</td>"
            f"<td>{html.escape(str(r.get('notes') or ''))}</td></tr>"
        )
    results_rows = "".join(result_lines) or "<tr><td colspan='4'>Нет опубликованных результатов</td></tr>"

    readiness = bundle.readiness
    ready_label = "готов" if readiness.official_ready else "черновик"
    warnings = "".join(f"<li>{html.escape(w)}</li>" for w in readiness.warnings)
    blockers = "".join(f"<li>{html.escape(b)}</li>" for b in readiness.blockers)

    generated = html.escape(bundle.generated_at.isoformat())

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <title>Официальный протокол — {title}</title>
  <style>
    body {{ font-family: Georgia, "Times New Roman", serif; margin: 2rem; color: #111; }}
    h1, h2 {{ margin: 0 0 0.5rem; }}
    .meta {{ color: #444; margin-bottom: 1.5rem; }}
    table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.45rem 0.6rem; text-align: left; }}
    th {{ background: #f5f5f5; }}
    .badge {{ display: inline-block; padding: 0.15rem 0.5rem; border: 1px solid #888; border-radius: 4px; }}
    @media print {{ body {{ margin: 1rem; }} }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">
    slug: {slug} · площадка: {venue} · дисциплины: {disciplines}<br />
    статус события: {status} · протокол: <span class="badge">{ready_label}</span><br />
    организация: {gov} · санкция: {sanction} · скоринг: {scoring_mode} · engine: {engine}<br />
    сформировано: {generated}
  </p>

  <h2>Судейская коллегия</h2>
  <table>
    <thead><tr><th>ФИО</th><th>Должность</th><th>Регион</th></tr></thead>
    <tbody>{officials_rows}</tbody>
  </table>

  <h2>Опубликованные результаты</h2>
  <table>
    <thead><tr><th>Место</th><th>Участник</th><th>Балл</th><th>Примечание</th></tr></thead>
    <tbody>{results_rows}</tbody>
  </table>

  <h2>Готовность протокола</h2>
  <ul>
    <li>Опубликованных результатов: {readiness.published_results_count}</li>
    <li>Опубликованных вложений протокола: {readiness.published_protocol_captures_count}</li>
  </ul>
  {"<h3>Предупреждения</h3><ul>" + warnings + "</ul>" if warnings else ""}
  {"<h3>Блокеры</h3><ul>" + blockers + "</ul>" if blockers else ""}

  <p class="meta">MyWave Event App · official protocol export v{bundle.format_version}</p>
</body>
</html>"""
