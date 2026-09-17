"""Import Center + Athlete claim tests. Fixtures are synthetic — no real PII."""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import select

from app.models.athlete import AccountAthleteLink, AthleteProfile
from app.models.participant import Participant
from app.models.user import User
from conftest import auth_header


def _xlsx_form(*rows: tuple) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Ответы"
    ws.append(
        [
            "ФИО",
            "Латинскими",
            "Дата рождения",
            "Телефон",
            "Регион",
            "Дисциплина",
            "Категория",
            "Медицинская справка",
        ]
    )
    for row in rows:
        ws.append(list(row))
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _event(client, org, slug: str = "import-cup") -> int:
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": slug, "title": "Import Cup", "status": "draft"},
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "registration_open"},
    )
    return event_id


def test_participant_cannot_import(client):
    org = auth_header(client, "imp-org-deny@example.com", "organizer")
    part = auth_header(client, "imp-part-deny@example.com", "participant")
    event_id = _event(client, org, "import-deny")
    payload = _xlsx_form(
        ("Тестов Тест", "Testov Test", "2000-01-01", "+79001110001", "Москва", "Вейкборд - катер", "Open", "https://example.com/m")
    )
    denied = client.post(
        f"/api/v1/events/{event_id}/imports",
        headers=part,
        files={"file": ("form.xlsx", payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert denied.status_code == 403


def test_import_idempotent_and_commit_creates_athlete_id(client, db_session):
    org = auth_header(client, "imp-org@example.com", "organizer")
    event_id = _event(client, org, "import-idemp")
    payload = _xlsx_form(
        ("Атлет Один", "Atlet One", "2001-05-05", "+79001110011", "Казань", "Вейкборд - катер", "Open Men", "scan"),
        ("Атлет Один", "Atlet One", "2001-05-05", "+79001110011", "Казань", "Wakesurf", "Open Men", "scan"),
        ("Атлет Два", "Atlet Two", "2012-02-02", "+79001110012", "Уфа", "неизвестная дисциплина", "U14", ""),
    )
    first = client.post(
        f"/api/v1/events/{event_id}/imports",
        headers=org,
        files={"file": ("form.xlsx", payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["row_count"] == 3
    assert body["new_count"] >= 1
    assert body["conflict_count"] >= 1
    batch_id = body["id"]
    rows = {row["display_name"]: row for row in body["rows"]}
    assert "repeat_application" in rows["Атлет Один"]["conflict_codes"] or rows["Атлет Один"]["match_kind"] in {
        "new",
        "probable",
    }
    assert rows["Атлет Два"]["match_kind"] == "conflict"
    assert "unknown_discipline" in rows["Атлет Два"]["conflict_codes"]
    assert all("+" not in (row.get("phone_masked") or "")[2:] or "***" in (row.get("phone_masked") or "") for row in body["rows"])

    second = client.post(
        f"/api/v1/events/{event_id}/imports",
        headers=org,
        files={"file": ("form.xlsx", payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert second.status_code == 200
    assert second.json()["id"] == batch_id

    committed = client.post(
        f"/api/v1/events/{event_id}/imports/{batch_id}/commit",
        headers=org,
    )
    assert committed.status_code == 200, committed.text
    assert committed.json()["status"] == "committed"
    assert committed.json()["committed_count"] >= 1

    again = client.post(
        f"/api/v1/events/{event_id}/imports/{batch_id}/commit",
        headers=org,
    )
    assert again.json()["committed_count"] == committed.json()["committed_count"]

    profiles = list(db_session.scalars(select(AthleteProfile)).all())
    assert any(p.athlete_id.startswith("MW-") for p in profiles)
    participants = list(
        db_session.scalars(select(Participant).where(Participant.event_id == event_id)).all()
    )
    assert len(participants) >= 1
    assert all(p.user_id is None for p in participants)
    assert all(p.athlete_profile_id is not None for p in participants)

    roster = client.get(f"/api/v1/events/{event_id}/participants", headers=org)
    assert roster.status_code == 200
    assert any(item.get("athlete_id", "").startswith("MW-") for item in roster.json()["items"])


def test_pending_claim_otp_and_confirm(client, db_session):
    org = auth_header(client, "imp-claim-org@example.com", "organizer")
    event_id = _event(client, org, "import-claim")
    phone = "+79001110021"
    payload = _xlsx_form(
        ("Клейм Спортсмен", "Claim Athlete", "1999-09-09", phone, "Пермь", "Wakeskim", "Open", "yes"),
    )
    uploaded = client.post(
        f"/api/v1/events/{event_id}/imports",
        headers=org,
        files={"file": ("claim.xlsx", payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert uploaded.status_code == 200, uploaded.text
    batch_id = uploaded.json()["id"]
    client.post(f"/api/v1/events/{event_id}/imports/{batch_id}/commit", headers=org)

    pending_user = db_session.scalar(select(User).where(User.phone == phone))
    assert pending_user is not None
    assert pending_user.status == "pending_claim"

    otp_req = client.post("/api/v1/auth/phone/request-otp", json={"phone": phone})
    assert otp_req.status_code == 200, otp_req.text
    code = otp_req.json()["dev_otp"]
    assert code

    verify = client.post("/api/v1/auth/phone/verify-otp", json={"phone": phone, "code": code})
    assert verify.status_code == 200, verify.text
    token = verify.json()["access_token"]
    assert verify.json()["status"] == "pending_claim"
    headers = {"Authorization": f"Bearer {token}"}

    links = client.get("/api/v1/me/athlete-links", headers=headers)
    assert links.status_code == 200
    assert links.json()["total"] >= 1
    link_id = links.json()["items"][0]["id"]
    athlete_id = links.json()["items"][0]["athlete_id"]
    assert athlete_id.startswith("MW-")

    confirmed = client.post(f"/api/v1/me/athlete-links/{link_id}/confirm", headers=headers)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"

    me = client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["status"] == "active"
    assert me.json()["athlete_id"] == athlete_id

    register = client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone,
            "email": "takeover@example.com",
            "display_name": "Чужой",
            "requested_role": "participant",
            "accept_terms": True,
            "accept_privacy": True,
        },
    )
    assert register.status_code == 409
    assert register.json()["error"]["code"] == "phone_taken"

    other = auth_header(client, "imp-other@example.com", "participant")
    stolen = client.post(f"/api/v1/me/athlete-links/{link_id}/confirm", headers=other)
    assert stolen.status_code == 404


def test_shared_phone_creates_two_links(client, db_session):
    org = auth_header(client, "imp-guard-org@example.com", "organizer")
    event_id = _event(client, org, "import-guard")
    phone = "+79001110031"
    payload = _xlsx_form(
        ("Родитель Тест", "Parent Test", "1980-01-01", phone, "Сочи", "Wakesurf", "Open", "yes"),
        ("Ребёнок Тест", "Child Test", "2014-01-01", phone, "Сочи", "Wakesurf", "U14", "yes"),
    )
    uploaded = client.post(
        f"/api/v1/events/{event_id}/imports",
        headers=org,
        files={"file": ("guard.xlsx", payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    batch_id = uploaded.json()["id"]
    client.post(f"/api/v1/events/{event_id}/imports/{batch_id}/commit", headers=org)
    user = db_session.scalar(select(User).where(User.phone == phone))
    assert user is not None
    links = list(
        db_session.scalars(select(AccountAthleteLink).where(AccountAthleteLink.user_id == user.id)).all()
    )
    assert len(links) == 2


def test_restricted_document_hidden_from_participant(client, tmp_path, monkeypatch):
    org = auth_header(client, "imp-doc-org@example.com", "organizer")
    part = auth_header(client, "imp-doc-part@example.com", "participant")
    event_id = _event(client, org, "import-docs")

    from app.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(Settings, "repo_root", property(lambda self: tmp_path))
    get_settings.cache_clear()
    (tmp_path / "data" / "documents").mkdir(parents=True, exist_ok=True)

    pdf = BytesIO(b"%PDF-1.4 medical placeholder")
    upload = client.post(
        f"/api/v1/events/{event_id}/documents",
        headers=org,
        files={"file": ("med.pdf", pdf, "application/pdf")},
        data={"title": "Медсправка", "kind": "other", "access_class": "medical-restricted"},
    )
    assert upload.status_code == 201, upload.text
    doc_id = upload.json()["id"]
    listed = client.get(f"/api/v1/events/{event_id}/documents", headers=part)
    assert listed.status_code == 200
    assert all(item["id"] != doc_id for item in listed.json()["items"])
    denied = client.get(f"/api/v1/events/{event_id}/documents/{doc_id}/file", headers=part)
    assert denied.status_code == 403
