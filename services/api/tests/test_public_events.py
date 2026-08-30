"""Public event showcase (J4) — no auth required for published events."""

from __future__ import annotations

from conftest import auth_header


def test_guest_lists_published_events_not_drafts(client):
    org = auth_header(client, "pub-org@example.com", "organizer")
    draft = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "guest-draft", "title": "Hidden draft", "status": "draft"},
    )
    assert draft.status_code == 201
    draft_id = draft.json()["id"]

    pub = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "guest-visible", "title": "Visible cup", "status": "published"},
    )
    assert pub.status_code == 201
    pub_id = pub.json()["id"]

    listed = client.get("/api/v1/events")
    assert listed.status_code == 200, listed.text
    ids = {item["id"] for item in listed.json()["items"]}
    assert pub_id in ids
    assert draft_id not in ids

    assert client.get(f"/api/v1/events/{pub_id}").status_code == 200
    assert client.get(f"/api/v1/events/{draft_id}").status_code == 404
    assert client.get(f"/api/v1/events/{pub_id}/detail").status_code == 200
    assert client.get(f"/api/v1/events/{pub_id}/categories").status_code == 200
    assert client.get(f"/api/v1/events/{pub_id}/officials").status_code == 200

    results = client.get(f"/api/v1/events/{pub_id}/results")
    assert results.status_code == 200
    assert all(row["status"] == "published" for row in results.json()["items"])


def test_guest_cannot_mutate_event(client):
    org = auth_header(client, "pub-org2@example.com", "organizer")
    pub = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "guest-mutate", "title": "No mutate", "status": "published"},
    )
    event_id = pub.json()["id"]
    denied = client.patch(
        f"/api/v1/events/{event_id}/status",
        json={"status": "live"},
    )
    assert denied.status_code == 401


def test_invalid_bearer_treated_as_guest_on_public_get(client):
    org = auth_header(client, "pub-org3@example.com", "organizer")
    pub = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "guest-expired", "title": "Expired token cup", "status": "published"},
    )
    assert pub.status_code == 201
    event_id = pub.json()["id"]

    listed = client.get("/api/v1/events", headers={"Authorization": "Bearer totally-invalid"})
    assert listed.status_code == 200, listed.text
    ids = {item["id"] for item in listed.json()["items"]}
    assert event_id in ids

    detail = client.get(
        f"/api/v1/events/{event_id}/detail",
        headers={"Authorization": "Bearer totally-invalid"},
    )
    assert detail.status_code == 200, detail.text


def test_guest_can_list_heats_on_published_event(client):
    org = auth_header(client, "pub-org4@example.com", "organizer")
    pub = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "guest-heats", "title": "Live heats cup", "status": "live"},
    )
    assert pub.status_code == 201
    event_id = pub.json()["id"]
    created = client.post(
        f"/api/v1/events/{event_id}/heats",
        headers=org,
        json={"code": "H1", "title": "Заезд 1", "heat_number": 1},
    )
    assert created.status_code == 201, created.text

    heats = client.get(f"/api/v1/events/{event_id}/heats")
    assert heats.status_code == 200, heats.text
    assert heats.json()["items"][0]["code"] == "H1"

    start_list = client.get(f"/api/v1/events/{event_id}/heats/{created.json()['id']}/start-list")
    assert start_list.status_code == 401

