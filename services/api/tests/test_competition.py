"""Competition endpoints + phone privacy."""

from __future__ import annotations

from conftest import auth_header


def _ensure_event(client, headers):
    response = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "slug": "privacy-cup",
            "title": "Privacy Cup",
            "city": "Kazan",
            "status": "published",
        },
    )
    assert response.status_code in {200, 201}, response.text
    return response.json()["id"]


def test_participants_do_not_expose_phone(client, db_session):
    from app.models.participant import Participant

    headers = auth_header(client, "organizer@example.com", "organizer")
    event_id = _ensure_event(client, headers)

    db_session.add(
        Participant(
            event_id=event_id,
            full_name="Секретный Участник",
            phone="+79005554433",
            status="registered",
            has_medical_cert=True,
            medical_cert_url="https://drive.google.com/secret-file",
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/events/{event_id}/participants", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    for item in body["items"]:
        assert "phone" not in item
        assert "medical_cert_url" not in item
        if item["full_name"] == "Секретный Участник":
            assert item["has_medical_cert"] is True


def test_schedule_hint_follows_this_event_not_kazan_stub(client):
    org = auth_header(client, "hint-org@example.com", "organizer")
    event_id = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": "moscow-wake-hint",
            "title": "Всероссийские соревнования по Вейкборду",
            "city": "Москва",
            "venue": "СберСити",
            "disciplines": "Вейкборд (катер)",
            "starts_at": "2026-09-05T00:00:00+00:00",
            "ends_at": "2026-09-06T00:00:00+00:00",
            "status": "draft",
        },
    ).json()["id"]
    response = client.get(f"/api/v1/events/{event_id}/schedule-hint", headers=org)
    assert response.status_code == 200, response.text
    body = response.json()
    text = body["summary"] + " " + " ".join(body["notes"])
    assert "Кабан" not in text
    assert "Торфяная" not in text
    assert "Excel" not in text
    assert "Москва" in body["summary"]
    assert "05.09.2026" in body["summary"]
    assert "06.09.2026" in body["summary"]
    assert "0" in " ".join(body["notes"])


def test_schedule_hint_kazan_title_gets_bulletin_program(client):
    org = auth_header(client, "hint-kazan@example.com", "organizer")
    event_id = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": "chr-pr-kazan-hint",
            "title": "Чемпионат России в Казани 2026",
            "city": "Казань",
            "status": "draft",
        },
    ).json()["id"]
    body = client.get(f"/api/v1/events/{event_id}/schedule-hint", headers=org).json()
    text = " ".join(body["notes"])
    assert "Нижний Кабан" in text
    assert "Казань" in body["summary"]
