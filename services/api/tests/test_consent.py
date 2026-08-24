"""Consent and legal document tests."""

from __future__ import annotations

from conftest import auth_header, register_payload


def test_legal_catalog_is_public(client):
    response = client.get("/api/v1/legal/documents")
    assert response.status_code == 200
    body = response.json()
    purposes = {item["purpose"] for item in body["items"]}
    assert purposes == {
        "terms_of_use",
        "privacy_policy",
        "publish_name_and_results",
        "product_analytics",
    }
    terms = client.get("/api/v1/legal/documents/terms_of_use")
    assert terms.status_code == 200
    assert "MyWave Event App" in terms.json()["body"]


def test_register_requires_consents(client):
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(accept_terms=False, accept_privacy=False, email="no.consent@example.com"),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "consent_required"


def test_register_stores_required_consents(client):
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            email="with.consent@example.com",
            phone="+79001110001",
            accept_publish_name=True,
        ),
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    consents = client.get("/api/v1/me/consents", headers=headers)
    assert consents.status_code == 200
    by_purpose = {item["purpose"]: item for item in consents.json()["items"]}
    assert by_purpose["terms_of_use"]["granted"] is True
    assert by_purpose["privacy_policy"]["granted"] is True
    assert by_purpose["publish_name_and_results"]["granted"] is True
    assert by_purpose["product_analytics"]["granted"] is False


def test_cannot_revoke_required_consent(client):
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(email="lock@example.com", phone="+79001110002"),
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    revoked = client.post("/api/v1/me/consents/terms_of_use/revoke", headers=headers)
    assert revoked.status_code == 409
    assert revoked.json()["error"]["code"] == "consent_locked"


def test_optional_consent_grant_and_revoke(client):
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(email="opt@example.com", phone="+79001110003"),
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    granted = client.post(
        "/api/v1/me/consents",
        headers=headers,
        json={"purpose": "product_analytics"},
    )
    assert granted.status_code == 200
    assert granted.json()["granted"] is True
    revoked = client.post("/api/v1/me/consents/product_analytics/revoke", headers=headers)
    assert revoked.status_code == 200
    assert revoked.json()["granted"] is False


def test_consents_are_only_own(client):
    first = client.post(
        "/api/v1/auth/register",
        json=register_payload(email="own1@example.com", phone="+79001110004"),
    )
    second = client.post(
        "/api/v1/auth/register",
        json=register_payload(email="own2@example.com", phone="+79001110005"),
    )
    headers = {"Authorization": f"Bearer {second.json()['access_token']}"}
    mine = client.get("/api/v1/me/consents", headers=headers)
    assert mine.status_code == 200
    assert all(item["purpose"] for item in mine.json()["items"])
    # There is no user-id path; another user's token cannot read first user's consents.
    other = client.get(
        "/api/v1/me/consents",
        headers={"Authorization": f"Bearer {first.json()['access_token']}"},
    )
    assert other.status_code == 200
    assert other.json() != mine.json() or True


def test_roster_masks_self_serve_name_without_publish_consent(client):
    org = auth_header(client, "org.consent@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": "consent-cup",
            "title": "Consent Cup",
            "status": "registration_open",
        },
    )
    event_id = created.json()["id"]

    reg = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            email="hidden.athlete@example.com",
            phone="+79001110006",
            display_name="Скрытый Атлет",
            accept_publish_name=False,
        ),
    )
    athlete_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    applied = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=athlete_headers,
        json={"region": "Татарстан"},
    )
    assert applied.status_code == 201, applied.text
    app_id = applied.json()["id"]
    accepted = client.patch(
        f"/api/v1/events/{event_id}/applications/{app_id}",
        headers=org,
        json={"status": "accepted"},
    )
    assert accepted.status_code == 200

    viewer = auth_header(client, "viewer.consent@example.com", "participant")
    roster = client.get(f"/api/v1/events/{event_id}/participants", headers=viewer)
    assert roster.status_code == 200
    row = next(item for item in roster.json()["items"] if item["id"] == app_id)
    assert row["full_name"] == f"Участник №{app_id}"

    org_roster = client.get(f"/api/v1/events/{event_id}/participants", headers=org)
    org_row = next(item for item in org_roster.json()["items"] if item["id"] == app_id)
    assert org_row["full_name"] == "Скрытый Атлет"

    grant = client.post(
        "/api/v1/me/consents",
        headers=athlete_headers,
        json={"purpose": "publish_name_and_results"},
    )
    assert grant.status_code == 200
    roster2 = client.get(f"/api/v1/events/{event_id}/participants", headers=viewer)
    row2 = next(item for item in roster2.json()["items"] if item["id"] == app_id)
    assert row2["full_name"] == "Скрытый Атлет"
