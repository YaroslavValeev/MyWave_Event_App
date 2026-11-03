"""Native PDF / DOCX export for official protocol snapshots (ADR-0017 extension)."""

from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def load_snapshot(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def _event_title(snapshot: dict[str, Any]) -> str:
    event = snapshot.get("event") or {}
    return str(event.get("title") or "Официальный протокол")


def _meta_lines(snapshot: dict[str, Any], *, revision_no: int | None = None) -> list[str]:
    event = snapshot.get("event") or {}
    readiness = snapshot.get("readiness") or {}
    lines = [
        f"Событие: {_event_title(snapshot)}",
        f"Slug: {event.get('slug') or '—'}",
        f"Статус события: {event.get('status') or '—'}",
        f"Место: {', '.join(x for x in [event.get('city'), event.get('venue'), event.get('location')] if x) or '—'}",
        f"Дисциплины: {event.get('disciplines') or '—'}",
        f"Движок: {snapshot.get('scoring_engine') or '—'}",
        f"Готовность: {'готов' if readiness.get('official_ready') else 'черновик'}",
        f"Сформировано: {snapshot.get('generated_at') or datetime.utcnow().isoformat()}",
        f"Генератор: {snapshot.get('generator') or 'MyWave Event App'}",
    ]
    if revision_no is not None:
        lines.insert(0, f"Ревизия протокола № {revision_no}")
        lines.append("Статус документа: утверждённый снимок (immutable)")
    else:
        lines.append("Статус документа: live-просмотр (не ревизия)")
    return lines


def _published_results(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    participants = {p.get("id"): p for p in (snapshot.get("participants") or [])}
    rows: list[dict[str, Any]] = []
    for r in snapshot.get("results") or []:
        if r.get("status") != "published":
            continue
        pid = r.get("participant_id")
        part = participants.get(pid) or {}
        rows.append(
            {
                "place": r.get("place"),
                "name": part.get("full_name") or part.get("name_latin") or f"#{pid}",
                "score": r.get("score"),
                "notes": r.get("notes") or "",
            }
        )
    rows.sort(key=lambda x: (x["place"] is None, x["place"] or 9999, str(x["name"])))
    return rows


def render_protocol_pdf(
    snapshot: dict[str, Any],
    *,
    revision_no: int | None = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=_event_title(snapshot),
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ProtoTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=8,
        textColor=colors.HexColor("#0f766e"),
    )
    body = ParagraphStyle("ProtoBody", parent=styles["Normal"], fontSize=10, leading=14)
    small = ParagraphStyle("ProtoSmall", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    story: list[Any] = [
        Paragraph("Официальный протокол соревнования", title_style),
        Paragraph(_event_title(snapshot), styles["Heading2"]),
        Spacer(1, 6),
    ]
    for line in _meta_lines(snapshot, revision_no=revision_no):
        story.append(Paragraph(line.replace("&", "&amp;"), body))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Судейская коллегия", styles["Heading3"]))

    officials = snapshot.get("officials") or []
    if officials:
        data = [["ФИО", "Должность", "Регион"]]
        for o in officials:
            data.append(
                [
                    str(o.get("full_name") or "—"),
                    str(o.get("position") or "—"),
                    str(o.get("region") or "—"),
                ]
            )
        table = Table(data, colWidths=[70 * mm, 50 * mm, 40 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ccfbf1")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#99f6e4")),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("—", body))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Опубликованные результаты", styles["Heading3"]))
    results = _published_results(snapshot)
    data = [["Место", "Участник", "Очки", "Примечание"]]
    for r in results:
        data.append(
            [
                str(r["place"] if r["place"] is not None else "—"),
                str(r["name"]),
                str(r["score"] if r["score"] is not None else "—"),
                str(r["notes"])[:80],
            ]
        )
    if len(data) == 1:
        data.append(["—", "Нет опубликованных результатов", "—", ""])
    table = Table(data, colWidths=[18 * mm, 70 * mm, 25 * mm, 47 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ccfbf1")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#99f6e4")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            "Документ сформирован автоматически. Юридическая официальность — только после "
            "утверждения ревизии уполномоченным лицом.",
            small,
        )
    )
    doc.build(story)
    return buffer.getvalue()


def render_protocol_docx(
    snapshot: dict[str, Any],
    *,
    revision_no: int | None = None,
) -> bytes:
    document = Document()
    document.add_heading("Официальный протокол соревнования", level=0)
    document.add_heading(_event_title(snapshot), level=1)
    for line in _meta_lines(snapshot, revision_no=revision_no):
        document.add_paragraph(line)

    document.add_heading("Судейская коллегия", level=2)
    officials = snapshot.get("officials") or []
    if officials:
        table = document.add_table(rows=1, cols=3)
        hdr = table.rows[0].cells
        hdr[0].text = "ФИО"
        hdr[1].text = "Должность"
        hdr[2].text = "Регион"
        for o in officials:
            row = table.add_row().cells
            row[0].text = str(o.get("full_name") or "—")
            row[1].text = str(o.get("position") or "—")
            row[2].text = str(o.get("region") or "—")
    else:
        document.add_paragraph("—")

    document.add_heading("Опубликованные результаты", level=2)
    results = _published_results(snapshot)
    table = document.add_table(rows=1, cols=4)
    hdr = table.rows[0].cells
    hdr[0].text = "Место"
    hdr[1].text = "Участник"
    hdr[2].text = "Очки"
    hdr[3].text = "Примечание"
    if not results:
        row = table.add_row().cells
        row[0].text = "—"
        row[1].text = "Нет опубликованных результатов"
        row[2].text = "—"
        row[3].text = ""
    for r in results:
        row = table.add_row().cells
        row[0].text = str(r["place"] if r["place"] is not None else "—")
        row[1].text = str(r["name"])
        row[2].text = str(r["score"] if r["score"] is not None else "—")
        row[3].text = str(r["notes"])[:120]

    note = document.add_paragraph(
        "Документ сформирован автоматически. Юридическая официальность — только после "
        "утверждения ревизии уполномоченным лицом."
    )
    note.alignment = WD_ALIGN_PARAGRAPH.LEFT

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
