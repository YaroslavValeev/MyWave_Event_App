"""Physical field actions ↔ app actions ↔ role handoffs (ADR-0012).

SoT цифр остаётся в Event App; эта матрица переводит «что делают руками на площадке»
в цифровые шаги и передачу следующей роли.
"""

from __future__ import annotations

from typing import Any

# phase: prep | day | after
ROLE_PHYSICAL_ACTIONS: tuple[dict[str, Any], ...] = (
    {
        "code": "docs_desk",
        "phase": "prep",
        "physical_ru": "Проверить бумажные/PDF документы события на стойке оргкомитета",
        "role": "organizer",
        "app_action": "documents upload + checklist.documents",
        "handoff_to": "judge",
        "notify_kinds": ["checklist.update"],
    },
    {
        "code": "medical_gate",
        "phase": "prep",
        "physical_ru": "Сверить медсправки / медфлаги до допуска на воду",
        "role": "organizer",
        "app_action": "checklist.medical / day_medical_gate",
        "handoff_to": "registrar",
        "notify_kinds": [],
    },
    {
        "code": "role_badge",
        "phase": "prep",
        "physical_ru": "Выдать бейдж / допуск судье или комментатору",
        "role": "organizer",
        "app_action": "admin approvals (role approve)",
        "handoff_to": "judge",
        "notify_kinds": ["role.approved"],
    },
    {
        "code": "checkin_desk",
        "phase": "day",
        "physical_ru": "Check-in участника на стойке (документы, bib)",
        "role": "organizer",
        "app_action": "start_list status → checked_in",
        "handoff_to": "judge",
        "notify_kinds": ["start_list.checked_in"],
    },
    {
        "code": "call_to_dock",
        "phase": "day",
        "physical_ru": "Вызвать спортсмена к понтону / зоне старта",
        "role": "support",
        "app_action": "start_list status → ready",
        "handoff_to": "judge",
        "notify_kinds": [],
    },
    {
        "code": "launch_on_water",
        "phase": "day",
        "physical_ru": "Выпустить на воду / дать старт заезду",
        "role": "judge",
        "app_action": "start_list / run status → on_water",
        "handoff_to": "judge",
        "notify_kinds": [],
    },
    {
        "code": "dns_mark",
        "phase": "day",
        "physical_ru": "Зафиксировать неявку у воды или на старте",
        "role": "organizer",
        "app_action": "start_list status → dns",
        "handoff_to": "commentator",
        "notify_kinds": [],
    },
    {
        "code": "dnf_mark",
        "phase": "day",
        "physical_ru": "Зафиксировать сход на воде",
        "role": "judge",
        "app_action": "start_list / run status → dnf",
        "handoff_to": "organizer",
        "notify_kinds": [],
    },
    {
        "code": "score_sheet",
        "phase": "day",
        "physical_ru": "Выставить оценки (планшет или бумажный лист → фото)",
        "role": "judge",
        "app_action": "judge-scores submit / protocol-capture",
        "handoff_to": "organizer",
        "notify_kinds": [],
    },
    {
        "code": "verify_publish",
        "phase": "day",
        "physical_ru": "Сверить панель судей и объявить / утвердить место",
        "role": "organizer",
        "app_action": "results verified → published",
        "handoff_to": "commentator",
        "notify_kinds": ["result.published"],
    },
    {
        "code": "field_moment",
        "phase": "day",
        "physical_ru": "Снять ключевой кадр / короткую заметку с понтона",
        "role": "commentator",
        "app_action": "field moment / report note (когда слой media wired)",
        "handoff_to": "organizer",
        "notify_kinds": [],
    },
    {
        "code": "protocol_pack",
        "phase": "after",
        "physical_ru": "Собрать официальный протокол (подпись / печать при необходимости)",
        "role": "organizer",
        "app_action": "official-protocol export + checklist.day_protocol_filed",
        "handoff_to": "federation_manager",
        "notify_kinds": [],
    },
    {
        "code": "event_report",
        "phase": "after",
        "physical_ru": "Вычитать хронику дня и отдать отчёт (не писать Excel с нуля)",
        "role": "organizer",
        "app_action": "event-report assemble (AI) → publish + excel download",
        "handoff_to": "federation_manager",
        "notify_kinds": ["event_report.published"],
    },
    {
        "code": "archive_lock",
        "phase": "after",
        "physical_ru": "Закрыть день: убрать live-правки, сдать архив",
        "role": "organizer",
        "app_action": "event status → completed (archive)",
        "handoff_to": "platform_admin",
        "notify_kinds": [],
    },
)


def list_role_physical_actions(*, phase: str | None = None, role: str | None = None) -> list[dict[str, Any]]:
    items = list(ROLE_PHYSICAL_ACTIONS)
    if phase:
        items = [i for i in items if i["phase"] == phase]
    if role:
        items = [i for i in items if i["role"] == role]
    return items


def actions_for_facts() -> list[dict[str, Any]]:
    """Compact copy for EventReport.facts_json."""
    return [
        {
            "code": i["code"],
            "phase": i["phase"],
            "physical_ru": i["physical_ru"],
            "role": i["role"],
            "app_action": i["app_action"],
            "handoff_to": i["handoff_to"],
        }
        for i in ROLE_PHYSICAL_ACTIONS
    ]
