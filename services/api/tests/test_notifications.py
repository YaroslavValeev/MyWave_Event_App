"""In-app notification log tests."""

from __future__ import annotations

from conftest import auth_header, register_payload


def test_role_pending_creates_notifications(client):
    org = auth_header(client, "org.notify@example.com", "organizer")
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79001230011",
            email="judge.notify@example.com",
            display_name="Судья Notify",
            requested_role="judge",
        ),
    )
    assert response.status_code == 200, response.text

    staff = client.get("/api/v1/me/notifications", headers=org)
    assert staff.status_code == 200
    kinds = {item["kind"] for item in staff.json()["items"]}
    assert "role.pending_staff" in kinds
    assert staff.json()["unread_count"] >= 1


def test_application_flow_notifies_athlete_and_staff(client):
    org = auth_header(client, "org.appnotify@example.com", "organizer")
    event = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": "notify-cup",
            "title": "Notify Cup",
            "status": "registration_open",
        },
    )
    assert event.status_code in {200, 201}, event.text
    event_id = event.json()["id"]

    reg = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79001230012",
            email="athlete.notify@example.com",
            display_name="Спортсмен Notify",
        ),
    )
    assert reg.status_code == 200
    athlete_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    created = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=athlete_headers,
        json={},
    )
    assert created.status_code in {200, 201}, created.text
    app_id = created.json()["id"]

    athlete_notes = client.get("/api/v1/me/notifications", headers=athlete_headers)
    assert athlete_notes.status_code == 200
    assert any(item["kind"] == "application.submitted" for item in athlete_notes.json()["items"])

    staff_notes = client.get("/api/v1/me/notifications", headers=org)
    assert any(item["kind"] == "application.submitted_staff" for item in staff_notes.json()["items"])

    decided = client.patch(
        f"/api/v1/events/{event_id}/applications/{app_id}",
        headers=org,
        json={"status": "accepted"},
    )
    assert decided.status_code == 200, decided.text

    after = client.get("/api/v1/me/notifications", headers=athlete_headers)
    assert any(item["kind"] == "application.accepted" for item in after.json()["items"])

    marked = client.post(
        f"/api/v1/me/notifications/{after.json()['items'][0]['id']}/read",
        headers=athlete_headers,
    )
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True
