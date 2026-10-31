"""AI narrative for EventReport draft.

Primary: local heuristic composer (no external dependency).
Optional: OpenAI Chat Completions when OPENAI_API_KEY is set.
Human publish remains mandatory (ADR-0012).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def render_ai_local_markdown(*, event_title: str, facts: dict[str, Any]) -> str:
    """Deterministic AI-style chronicle from structured facts."""
    podium = facts.get("podium") or []
    exceptions = facts.get("dns_dnf") or []
    officials = facts.get("officials") or []
    published_n = int(facts.get("published_results_count") or 0)
    heats_n = int(facts.get("heats_count") or 0)
    actions = facts.get("role_actions") or []

    lines: list[str] = [
        f"# Отчёт: {event_title}",
        "",
        f"_AI-черновик (local) · {facts.get('assembled_at', '')}_",
        "",
        "## Краткое резюме",
        "",
    ]
    if published_n == 0 and not exceptions:
        lines.append(
            f"Событие «{event_title}» ещё без опубликованных результатов. "
            "Черновик собран для подготовки хроники; дополните факты Live и пересоберите."
        )
    else:
        lines.append(
            f"В «{event_title}» зафиксировано заездов/heat: **{heats_n}**, "
            f"опубликованных результатов: **{published_n}**, "
            f"DNS/DNF: **{len(exceptions)}**."
        )
        if podium:
            leaders = ", ".join(
                f"{r.get('place')} место — {r.get('full_name')}" for r in podium[:3]
            )
            lines.append(f"Лидеры дня: {leaders}.")
        if exceptions:
            sample = ", ".join(
                f"{e.get('full_name')} ({str(e.get('status', '')).upper()})"
                for e in exceptions[:5]
            )
            lines.append(f"Исключения старта: {sample}.")
    lines.extend(["", "## Призёры", ""])
    if not podium:
        lines.append("_Нет опубликованных мест 1–3._")
    else:
        for row in podium:
            score = row.get("score")
            score_bit = f" — {score}" if score is not None else ""
            lines.append(f"{row.get('place')}. **{row.get('full_name')}**{score_bit}")

    lines.extend(["", "## DNS / DNF", ""])
    if not exceptions:
        lines.append("_Нет записей DNS/DNF._")
    else:
        for row in exceptions:
            heat = row.get("heat_code") or row.get("heat_id") or "—"
            lines.append(
                f"- {str(row.get('status', '?')).upper()}: **{row.get('full_name')}** (heat {heat})"
            )

    lines.extend(["", "## Судейская коллегия", ""])
    if not officials:
        lines.append("_Официалы не указаны._")
    else:
        for o in officials:
            lines.append(f"- {o.get('full_name')} — {o.get('position') or 'официал'}")

    day_actions = [a for a in actions if a.get("phase") == "day"]
    lines.extend(["", "## Передача действий на площадке", ""])
    if not day_actions:
        lines.append("_Матрица ролей не подключена._")
    else:
        for a in day_actions[:8]:
            lines.append(
                f"- **{a.get('role')}** → {a.get('handoff_to')}: {a.get('physical_ru')} "
                f"({a.get('app_action')})"
            )

    lines.extend(
        [
            "",
            "## Хроника (AI)",
            "",
            "День прошёл в цифровом контуре MyWave Event App: явка и статусы на старте, "
            "оценки судей и публикация мест без Excel как Source of Truth. "
            "Ниже — место для 2–3 человеческих правок (погода, атмосфера, инциденты).",
            "",
            "## Моменты",
            "",
            "_Полевые фото/видео появятся после approve media-слоя._",
            "",
            "> AI не публикует отчёт сам — нужна кнопка Publish организатора.",
            "",
        ]
    )
    return "\n".join(lines)


def render_ai_openai_markdown(
    *,
    event_title: str,
    facts: dict[str, Any],
    api_key: str,
    model: str,
    timeout_s: float = 45.0,
) -> str:
    """Call OpenAI chat completions; raises on transport/API errors."""
    system = (
        "Ты помощник секретаря соревнования wakeboard/wakesurf. "
        "Напиши отчёт на русском в Markdown: резюме, призёры, DNS/DNF, коллегия, "
        "краткая хроника, handoff ролей. Не выдумывай спортсменов и места вне JSON. "
        "Не публикуй отчёт — только черновик. Без эмодзи."
    )
    user = (
        f"Событие: {event_title}\n\nФакты JSON:\n"
        f"{json.dumps(facts, ensure_ascii=False)[:12000]}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.4,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
    content = data["choices"][0]["message"]["content"]
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("empty_openai_content")
    return content.strip() + "\n\n> AI-черновик OpenAI — Publish только человеком.\n"


def compose_ai_body(
    *,
    event_title: str,
    facts: dict[str, Any],
    openai_api_key: str | None,
    openai_model: str,
) -> tuple[str, str]:
    """Return (body_markdown, provider) where provider is openai|local."""
    key = (openai_api_key or "").strip()
    if key:
        try:
            body = render_ai_openai_markdown(
                event_title=event_title,
                facts=facts,
                api_key=key,
                model=openai_model,
            )
            return body, "openai"
        except Exception as exc:  # noqa: BLE001 — fallback to local AI
            logger.warning("OpenAI event report failed, fallback local: %s", exc)
    body = render_ai_local_markdown(event_title=event_title, facts=facts)
    return body, "local"
