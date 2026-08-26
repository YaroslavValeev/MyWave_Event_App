"""Athlete ID and archived event lock tests."""

from __future__ import annotations

from conftest import auth_header


def test_register_assigns_athlete_id(client):
    from conftest import register_payload

    response = client.post("/api/v1/auth/register", json=register_payload(email="ath1@example.com", phone="+79001112201"))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["athlete_id"]
    assert body["athlete_id"].startswith("MW-")
    assert len(body["athlete_id"]) == 11  # MW- + 8

    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["athlete_id"] == body["athlete_id"]


def test_dev_login_assigns_athlete_id(client):
    headers = auth_header(client, "ath-dev@example.com", "participant")
    me = client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["athlete_id"].startswith("MW-")


def test_participant_list_exposes_athlete_id(client):
    org = auth_header(client, "ath-org@example.com", "organizer")
    part = auth_header(client, "ath-part@example.com", "participant")
    event_id = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "ath-roster", "title": "Athlete Roster", "status": "draft"},
    ).json()["id"]
    client.patch(f"/api/v1/events/{event_id}/status", headers=org, json={"status": "registration_open"})
    app = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=part,
        json={"category_id": None},
    )
    assert app.status_code == 201, app.text
    pid = app.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/applications/{pid}",
        headers=org,
        json={"status": "accepted"},
    )
    me = client.get("/api/v1/me", headers=part).json()
    roster = client.get(f"/api/v1/events/{event_id}/participants", headers=org)
    assert roster.status_code == 200
    item = next(i for i in roster.json()["items"] if i["id"] == pid)
    assert item["athlete_id"] == me["athlete_id"]


def test_completed_event_is_read_only(client):
    org = auth_header(client, "arch-org@example.com", "organizer")
    event_id = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "arch-cup", "title": "Archive Cup", "status": "draft"},
    ).json()["id"]
    client.patch(f"/api/v1/events/{event_id}/status", headers=org, json={"status": "registration_open"})
    client.patch(f"/api/v1/events/{event_id}/status", headers=org, json={"status": "live"})
    client.patch(f"/api/v1/events/{event_id}/status", headers=org, json={"status": "completed"})

    detail = client.get(f"/api/v1/events/{event_id}/detail", headers=org)
    assert detail.status_code == 200
    assert detail.json()["archived"] is True

    blocked = client.post(
        f"/api/v1/events/{event_id}/heats",
        headers=org,
        json={"code": "H1", "title": "Heat 1", "heat_number": 1},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "event_archived"

    # Escape hatch: reopen via status change
    reopened = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "live"},
    )
    assert reopened.status_code == 200
    ok = client.post(
        f"/api/v1/events/{event_id}/heats",
        headers=org,
        json={"code": "H1", "title": "Heat 1", "heat_number": 1},
    )
    assert ok.status_code == 201, ok.text
