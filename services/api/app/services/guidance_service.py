"""Role-based journey guidance — computed over checklist + event state (ADR-0015)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.domain.role_physical_actions import ROLE_PHYSICAL_ACTIONS
from app.models.event import Event
from app.models.participant import Participant
from app.models.result import Result
from app.models.user import User
from app.services.checklist_service import ensure_checklist
from app.services.event_service import get_event, is_event_archived


def compute_journey_phase(event: Event, *, open_checklist: int, draft_or_verified: int) -> str:
    status = event.status
    if status == "draft":
        return "DRAFT" if open_checklist > 3 else "CONFIGURED"
    if status == "published":
        return "CONFIGURED"
    if status == "registration_open":
        return "REGISTRATION"
    if status == "live":
        if draft_or_verified > 0:
            return "RESULTS_REVIEW"
        return "LIVE"
    if status == "completed":
        return "ARCHIVED" if is_event_archived(event) else "OFFICIAL"
    if status == "cancelled":
        return "ARCHIVED"
    return "CONFIGURED"


def _role(user: User | None) -> Role | None:
    if user is None:
        return None
    try:
        return Role(user.role)
    except ValueError:
        return None


def build_guidance(
    db: Session,
    *,
    event_id: int,
    actor: User | None,
) -> dict[str, Any]:
    event = get_event(db, event_id=event_id, actor=actor)
    # Guest: no checklist side-effects — use empty if cannot auth
    checklist: list[Any] = []
    if actor is not None:
        checklist = ensure_checklist(db, event_id=event_id, actor=actor)

    open_items = [i for i in checklist if not i.is_done]
    done_items = [i for i in checklist if i.is_done]
    draft_or_verified = int(
        db.scalar(
            select(func.count())
            .select_from(Result)
            .where(
                Result.event_id == event_id,
                Result.status.in_(("draft", "verified")),
            )
        )
        or 0
    )
    published_count = int(
        db.scalar(
            select(func.count())
            .select_from(Result)
            .where(Result.event_id == event_id, Result.status == "published")
        )
        or 0
    )

    phase = compute_journey_phase(
        event, open_checklist=len(open_items), draft_or_verified=draft_or_verified
    )
    role = _role(actor)

    tasks: list[dict[str, Any]] = []
    completed: list[dict[str, Any]] = []

    for item in done_items[:8]:
        completed.append(
            {
                "id": f"checklist:{item.code}",
                "title": item.title,
                "kind": "checklist",
                "required": True,
            }
        )

    if role in EVENT_WRITE_ROLES or role == Role.platform_admin:
        for item in open_items[:6]:
            tasks.append(
                {
                    "id": f"checklist:{item.code}",
                    "title": item.title,
                    "kind": "checklist",
                    "required": True,
                    "requires_online": True,
                    "href": f"/events/{event_id}#checklist",
                    "urgency": "action_required",
                }
            )
        if draft_or_verified > 0:
            tasks.append(
                {
                    "id": "results:review",
                    "title": f"Проверить результаты на проверке ({draft_or_verified})",
                    "kind": "results",
                    "required": True,
                    "requires_online": True,
                    "href": f"/events/{event_id}#results",
                    "urgency": "action_required",
                }
            )
        if phase in {"LIVE", "RESULTS_REVIEW", "OFFICIAL"} and published_count > 0:
            tasks.append(
                {
                    "id": "protocol:snapshot",
                    "title": "Зафиксировать ревизию официального протокола",
                    "kind": "protocol",
                    "required": False,
                    "requires_online": True,
                    "href": f"/events/{event_id}#protocol",
                    "urgency": "recommended",
                }
            )

    if role == Role.judge:
        tasks.append(
            {
                "id": "judge:score",
                "title": "Ввести оценки в назначенном заезде",
                "kind": "scoring",
                "required": True,
                "requires_online": True,
                "href": f"/events/{event_id}#scoring",
                "urgency": "action_required",
            }
        )
        tasks.append(
            {
                "id": "judge:protocol-photo",
                "title": "При необходимости прикрепить фото судейского листа",
                "kind": "protocol",
                "required": False,
                "requires_online": True,
                "href": f"/events/{event_id}#protocol",
                "urgency": "recommended",
            }
        )

    if role == Role.participant:
        app_row = db.scalar(
            select(Participant).where(
                Participant.event_id == event_id,
                Participant.user_id == (actor.id if actor else -1),
            )
        )
        if app_row is None:
            tasks.append(
                {
                    "id": "participant:apply",
                    "title": "Подать заявку на участие",
                    "kind": "application",
                    "required": True,
                    "requires_online": True,
                    "href": f"/events/{event_id}#apps",
                    "urgency": "action_required",
                }
            )
        else:
            tasks.append(
                {
                    "id": "participant:status",
                    "title": f"Статус заявки: {app_row.status}",
                    "kind": "application",
                    "required": False,
                    "requires_online": True,
                    "href": f"/events/{event_id}#apps",
                    "urgency": "info",
                }
            )
        if published_count > 0:
            tasks.append(
                {
                    "id": "participant:results",
                    "title": "Посмотреть опубликованные результаты",
                    "kind": "results",
                    "required": False,
                    "requires_online": True,
                    "href": f"/events/{event_id}#results",
                    "urgency": "recommended",
                }
            )

    if role in {Role.media, Role.commentator}:
        tasks.append(
            {
                "id": "media:feed",
                "title": "Опубликовать пост в ленте мероприятия",
                "kind": "publication",
                "required": False,
                "requires_online": True,
                "href": f"/events/{event_id}#feed",
                "urgency": "recommended",
            }
        )

    if actor is None:
        tasks.append(
            {
                "id": "guest:scoreboard",
                "title": "Смотреть табло и опубликованные результаты",
                "kind": "scoreboard",
                "required": False,
                "requires_online": True,
                "href": f"/events/{event_id}#scoreboard",
                "urgency": "info",
            }
        )

    # Context tips from physical actions matrix (filtered by role + phase bucket)
    phase_bucket = "prep"
    if phase in {"LIVE", "RESULTS_REVIEW"}:
        phase_bucket = "day"
    elif phase in {"OFFICIAL", "ARCHIVED"}:
        phase_bucket = "after"

    tips: list[dict[str, Any]] = []
    for action in ROLE_PHYSICAL_ACTIONS:
        if action.get("phase") != phase_bucket:
            continue
        if role is not None and action.get("role") not in {role.value, "organizer"}:
            # show organizer tips only to write roles; role-matched otherwise
            if action.get("role") != role.value:
                if not (action.get("role") == "organizer" and role in EVENT_WRITE_ROLES):
                    continue
        tips.append(
            {
                "code": action["code"],
                "title": action["physical_ru"],
                "app_action": action.get("app_action"),
                "required": False,
            }
        )
        if len(tips) >= 5:
            break

    next_task = next((t for t in tasks if t.get("urgency") == "action_required"), None)
    if next_task is None and tasks:
        next_task = tasks[0]

    return {
        "event_id": event_id,
        "event_status": event.status,
        "journey_phase": phase,
        "role": role.value if role else "guest",
        "progress": {
            "checklist_done": len(done_items),
            "checklist_total": len(checklist),
            "published_results": published_count,
            "pending_results": draft_or_verified,
        },
        "next_step": next_task,
        "tasks": tasks,
        "completed": completed,
        "tips": tips,
        "offline_note": (
            "Без сети доступны только локальные черновики; шаги с requires_online "
            "нужно выполнить после восстановления связи."
        ),
    }
