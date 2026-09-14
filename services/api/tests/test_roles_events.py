"""Roles, events, and audit tests."""

from __future__ import annotations

from conftest import auth_header


def test_roles_catalog_includes_chief_judge(client):
    response = client.get("/api/v1/roles")
    assert response.status_code == 200
    body = response.json()
    assert "chief_judge" in body["items"]
    assert "organizer" in body["items"]
    assert body["total"] == len(body["items"])


def test_organizer_can_create_and_update_event(client):
    headers = auth_header(client, "org@example.com", "organizer")
    create = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "slug": "summer-cup",
            "title": "Summer Cup",
            "description": "Test event",
            "status": "draft",
        },
    )
    assert create.status_code == 201, create.text
    event = create.json()
    assert event["slug"] == "summer-cup"
    assert event["status"] == "draft"
    event_id = event["id"]

    patched = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers,
        json={"status": "published"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "published"

    listed = client.get("/api/v1/events", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1


def test_participant_cannot_create_event(client):
    headers = auth_header(client, "p@example.com", "participant")
    response = client.post(
        "/api/v1/events",
        headers=headers,
        json={"slug": "nope", "title": "Nope", "status": "draft"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_participant_reads_only_published(client):
    org = auth_header(client, "org2@example.com", "organizer")
    draft = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "hidden-draft", "title": "Hidden", "status": "draft"},
    )
    assert draft.status_code == 201
    draft_id = draft.json()["id"]

    pub = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "visible-pub", "title": "Visible", "status": "published"},
    )
    assert pub.status_code == 201
    pub_id = pub.json()["id"]

    part = auth_header(client, "viewer@example.com", "participant")
    listed = client.get("/api/v1/events", headers=part)
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["items"]}
    assert pub_id in ids
    assert draft_id not in ids

    assert client.get(f"/api/v1/events/{draft_id}", headers=part).status_code == 404
    assert client.get(f"/api/v1/events/{pub_id}", headers=part).status_code == 200


def test_audit_requires_admin_and_records_actions(client):
    org = auth_header(client, "audit-org@example.com", "organizer")
    client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "audit-event", "title": "Audit", "status": "draft"},
    )

    denied = client.get("/api/v1/audit", headers=org)
    assert denied.status_code == 403

    admin = auth_header(client, "admin@example.com", "platform_admin")
    audit = client.get("/api/v1/audit", headers=admin)
    assert audit.status_code == 200
    actions = {item["action"] for item in audit.json()["items"]}
    assert "auth.dev_login" in actions
    assert "event.create" in actions


def test_structured_error_shape(client):
    response = client.get("/api/v1/me")
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
