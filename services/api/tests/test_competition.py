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


def test_schedule_hint(client):
    headers = auth_header(client, "viewer@example.com", "participant")
    # participant cannot create; use organizer for event
    org = auth_header(client, "org2@example.com", "organizer")
    event_id = _ensure_event(client, org)
    response = client.get(f"/api/v1/events/{event_id}/schedule-hint", headers=headers)
    assert response.status_code == 200
    assert "summary" in response.json()
