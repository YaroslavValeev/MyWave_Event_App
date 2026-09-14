"""Document pack ingest: IWWF categories, start lists, KS officials. Synthetic fixtures only."""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from sqlalchemy import select

from app.models.category import Category
from app.models.heat import Heat, StartListEntry
from app.models.official import Official
from conftest import auth_header


STARTLIST_TEXT = """
Kazan Championship wakeboard
Under 14 Girls Wakeboard Qualifications Starting list Thursday - 10:00
Homologation: Not homologated
Name Team Categ. Score
1 Testova Anna U14 F
2 Petrova Maria U14 F
Junior Men Wakeboard Qualifications Starting list Thursday - 11:00
Homologation: Not homologated
Name Team Categ. Score
1 Ivanov Ivan Jun M
"""

KS_TEXT = """
ПРОТОКОЛ
заочного заседания Коллегии спортивных судей
от 13 июля 2026 г. № 32-КС
1 Главный судья Филиппов А. В. г. Санкт-Петербург ВК,МК
2 Главный секретарь Живаев С.В. Самарская область ВК
11 Судья комментатор Валеев Я. Республика Татарстан
"""


def _xlsx() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Вейкборд-катер"
    ws.append(["№", "ФИО", "Фамилия Имя (лат.)", "Дата рождения", "Пол", "Категория", "Регион", "Телефон"])
    ws.append([1, "Тестова Анна", "Testova Anna", "2014-01-01", "Ж", "Девочки U14", "Казань", "+79001112201"])
    ws.append([2, "Иванов Иван", "Ivanov Ivan", "2009-06-01", "М", "Юноши U18", "Казань", "+79001112202"])
    ws.append([3, "Сидоров Пётр", "Sidorov Petr", "1975-03-03", "М", "Мужчины", "Казань", "+79001112203"])
    sched = wb.create_sheet("Расписание (3 дня)")
    sched["A1"] = "РАСПИСАНИЕ"
    sched["A3"] = "ДЕНЬ 1 — 13.08.2026 · Квалификации"
    sched.append([])
    sched["A4"] = "10:00–10:14"
    sched["B4"] = "Вейкборд-катер"
    sched["C4"] = "Девочки U14"
    sched["D4"] = "Квалификация"
    sched["E4"] = "Заезд"
    sched["F4"] = 2
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _event(client, org, slug: str = "pack-kazan") -> int:
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": slug,
            "title": "Чемпионат России в Казани 2026",
            "city": "Казань",
            "status": "draft",
        },
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "registration_open"},
    )
    return event_id


def test_ingest_pack_xlsx_and_pdfs(client, db_session, monkeypatch):
    org = auth_header(client, "pack-org@example.com", "organizer")
    event_id = _event(client, org)

    def fake_text(payload: bytes) -> str:
        if payload.startswith(b"START"):
            return STARTLIST_TEXT
        return KS_TEXT

    monkeypatch.setattr("app.services.event_pack_service.extract_pdf_text", fake_text)

    response = client.post(
        f"/api/v1/events/{event_id}/ingest-pack",
        headers=org,
        files=[
            (
                "files",
                (
                    "Регистрация_ЧР_ПР_2026_по_категориям.xlsx",
                    _xlsx(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            ),
            ("files", ("u14_jun_wakeboard_qualifications_startlist.pdf", b"STARTLIST", "application/pdf")),
            ("files", ("32_протокол_КС_Казань.pdf", b"PROTOCOL", "application/pdf")),
        ],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["officials"] >= 3
    assert body["start_entries"] >= 3

    titles = [c.title for c in db_session.scalars(select(Category).where(Category.event_id == event_id)).all()]
    codes = [c.code for c in db_session.scalars(select(Category).where(Category.event_id == event_id)).all()]
    assert any("U14" in t for t in titles)
    assert any("U18" in t for t in titles)
    assert any("O40" in t for t in titles)
    assert "wb-u14-f" in codes
    assert "wb-u18-m" in codes
    assert "wb-o40-m" in codes

    heats = list(db_session.scalars(select(Heat).where(Heat.event_id == event_id)).all())
    assert heats
    entries = list(db_session.scalars(select(StartListEntry).where(StartListEntry.event_id == event_id)).all())
    assert len(entries) >= 3
    officials = list(db_session.scalars(select(Official).where(Official.event_id == event_id)).all())
    assert any("Филиппов" in o.full_name for o in officials)
