"""Event application (self-serve) tests."""

from __future__ import annotations

from conftest import auth_header, register_payload


def _create_open_event(client, headers):
    response = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "slug": "open-reg-cup",
            "title": "Open Registration Cup",
            "status": "registration_open",
        },
    )
    assert response.status_code in {200, 201}, response.text
    return response.json()["id"]


def test_apply_accept_flow(client):
    org = auth_header(client, "org.apply@example.com", "organizer")
    event_id = _create_open_event(client, org)

    # Register athlete with phone auth path
    reg = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79007770001",
            email="apply.athlete@example.com",
            display_name="Заявитель Тест",
        ),
    )
    assert reg.status_code == 200, reg.text
    athlete_token = reg.json()["access_token"]
    athlete_headers = {"Authorization": f"Bearer {athlete_token}"}

    created = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=athlete_headers,
        json={"region": "Татарстан", "club": "MyWave"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "pending"
    app_id = created.json()["id"]

    # Public roster hides pending
    roster = client.get(f"/api/v1/events/{event_id}/participants", headers=athlete_headers)
    assert roster.status_code == 200
    assert all(i["id"] != app_id for i in roster.json()["items"])
    assert all("phone" not in i for i in roster.json()["items"])

    mine = client.get(f"/api/v1/events/{event_id}/applications/me", headers=athlete_headers)
    assert mine.status_code == 200
    assert mine.json()["status"] == "pending"

    pending = client.get(f"/api/v1/events/{event_id}/applications", headers=org)
    assert pending.status_code == 200
    assert pending.json()["total"] >= 1

    accepted = client.patch(
        f"/api/v1/events/{event_id}/applications/{app_id}",
        headers=org,
        json={"status": "accepted"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    roster2 = client.get(f"/api/v1/events/{event_id}/participants", headers=athlete_headers)
    assert any(i["id"] == app_id for i in roster2.json()["items"])


def test_participant_cannot_list_pending(client):
    org = auth_header(client, "org2.apply@example.com", "organizer")
    event_id = _create_open_event(client, org)
    athlete = auth_header(client, "plain@example.com", "participant")
    response = client.get(f"/api/v1/events/{event_id}/applications", headers=athlete)
    assert response.status_code == 403
