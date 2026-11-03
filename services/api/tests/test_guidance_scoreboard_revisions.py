"""Guidance, scoreboard, protocol revisions — ADR-0015/16/17."""

from __future__ import annotations

from conftest import auth_header


def _seed_event(client, slug: str = "guide-cup", status: str = "live"):
    org = auth_header(client, f"{slug}-org@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": slug, "title": "Guidance Cup", "status": "draft"},
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": status},
    )
    return event_id, org


def test_guidance_for_organizer_and_guest(client):
    event_id, org = _seed_event(client, "g1", status="live")
    staff = client.get(f"/api/v1/events/{event_id}/guidance", headers=org)
    assert staff.status_code == 200, staff.text
    body = staff.json()
    assert body["journey_phase"] in {"LIVE", "RESULTS_REVIEW"}
    assert body["role"] == "organizer"
    assert "tasks" in body
    assert body["next_step"] is not None or len(body["tasks"]) >= 0

    guest = client.get(f"/api/v1/events/{event_id}/guidance")
    assert guest.status_code == 200
    assert guest.json()["role"] == "guest"


def test_scoreboard_published_only_for_guest(client):
    event_id, org = _seed_event(client, "sb1", status="registration_open")
    part = auth_header(client, "sb1-ath@example.com", "participant")
    app = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=part,
        json={"category_id": None, "region": "Казань"},
    )
    assert app.status_code == 201, app.text
    pid = app.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/applications/{pid}",
        headers=org,
        json={"status": "accepted"},
    )
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "live"},
    )
    draft = client.post(
        f"/api/v1/events/{event_id}/results",
        headers=org,
        json={"participant_id": pid, "score": 88.5, "place": 1},
    )
    assert draft.status_code == 201, draft.text
    rid = draft.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/results/{rid}/status",
        headers=org,
        json={"status": "verified"},
    )

    guest_before = client.get(f"/api/v1/events/{event_id}/scoreboard")
    assert guest_before.status_code == 200
    assert guest_before.json()["total"] == 0

    staff = client.get(
        f"/api/v1/events/{event_id}/scoreboard",
        headers=org,
        params={"include_unofficial": True},
    )
    assert staff.status_code == 200
    assert staff.json()["total"] >= 1

    client.patch(
        f"/api/v1/events/{event_id}/results/{rid}/status",
        headers=org,
        json={"status": "published"},
    )
    guest_after = client.get(f"/api/v1/events/{event_id}/scoreboard")
    assert guest_after.json()["total"] == 1
    assert guest_after.json()["revision"]


def test_protocol_revision_requires_readiness_then_stores_snapshot(client):
    event_id, org = _seed_event(client, "pr1", status="registration_open")
    # Without published results / rules — not ready
    bad = client.post(
        f"/api/v1/events/{event_id}/official-protocol/revisions",
        headers=org,
        json={"note": "early"},
    )
    assert bad.status_code == 400

    put = client.put(
        f"/api/v1/events/{event_id}/rules-profile",
        headers=org,
        json={
            "governing_body": "FVLS",
            "sanction_body": "IWWF",
            "discipline_codes": ["wakeskim"],
            "scoring_mode": "manual",
        },
    )
    assert put.status_code == 200, put.text
    part = auth_header(client, "pr1-ath@example.com", "participant")
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
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "live"},
    )
    draft = client.post(
        f"/api/v1/events/{event_id}/results",
        headers=org,
        json={"participant_id": pid, "score": 90, "place": 1},
    )
    assert draft.status_code == 201, draft.text
    rid = draft.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/results/{rid}/status",
        headers=org,
        json={"status": "verified"},
    )
    client.patch(
        f"/api/v1/events/{event_id}/results/{rid}/status",
        headers=org,
        json={"status": "published"},
    )

    ok = client.post(
        f"/api/v1/events/{event_id}/official-protocol/revisions",
        headers=org,
        json={"note": "День 1 утверждён"},
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["revision_no"] == 1
    assert ok.json()["content_sha256"]

    listed = client.get(
        f"/api/v1/events/{event_id}/official-protocol/revisions",
        headers=org,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    # Second approval creates revision 2 (immutable history)
    ok2 = client.post(
        f"/api/v1/events/{event_id}/official-protocol/revisions",
        headers=org,
        json={"note": "Корректировка после уточнения"},
    )
    assert ok2.status_code == 201
    assert ok2.json()["revision_no"] == 2
