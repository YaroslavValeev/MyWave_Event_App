"""SCORE-13C: Idempotency-Key + optimistic version on judge scores."""

from __future__ import annotations

from conftest import auth_header


def _seed_structured_event(client, slug: str):
    org = auth_header(client, f"{slug}-org@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": slug,
            "title": slug,
            "status": "draft",
            "rules_profile": {
                "governing_body": "FVLS",
                "sanction_body": "IWWF",
                "discipline_codes": ["wakesurf_boat"],
                "scoring_mode": "structured",
            },
        },
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "registration_open"},
    )
    athlete = auth_header(client, f"{slug}-ath@example.com", "participant")
    app = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=athlete,
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
    return org, event_id, pid


CRITERIA = {
    "difficulty": 80,
    "risk": 70,
    "intensity": 75,
    "variety": 65,
    "execution": 85,
}


def test_idempotency_key_returns_same_sheet(client):
    _, event_id, pid = _seed_structured_event(client, "score-idem-1")
    judge = auth_header(client, "score-idem-j@example.com", "judge")
    headers = {**judge, "Idempotency-Key": "sheet-op-1"}
    first = client.post(
        f"/api/v1/events/{event_id}/judge-scores",
        headers=headers,
        json={"participant_id": pid, "attempt_no": 1, "criteria": CRITERIA},
    )
    assert first.status_code == 201, first.text
    second = client.post(
        f"/api/v1/events/{event_id}/judge-scores",
        headers=headers,
        json={
            "participant_id": pid,
            "attempt_no": 1,
            "criteria": {**CRITERIA, "execution": 99},
        },
    )
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["total"] == first.json()["total"]
    assert second.json()["version"] == first.json()["version"]


def test_version_conflict_returns_409(client):
    _, event_id, pid = _seed_structured_event(client, "score-ver-1")
    judge = auth_header(client, "score-ver-j@example.com", "judge")
    created = client.post(
        f"/api/v1/events/{event_id}/judge-scores",
        headers=judge,
        json={"participant_id": pid, "attempt_no": 1, "criteria": CRITERIA},
    )
    assert created.status_code == 201, created.text
    assert created.json()["version"] == 1

    ok = client.post(
        f"/api/v1/events/{event_id}/judge-scores",
        headers=judge,
        json={
            "participant_id": pid,
            "attempt_no": 1,
            "criteria": {**CRITERIA, "risk": 71},
            "expected_version": 1,
        },
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["version"] == 2

    conflict = client.post(
        f"/api/v1/events/{event_id}/judge-scores",
        headers=judge,
        json={
            "participant_id": pid,
            "attempt_no": 1,
            "criteria": {**CRITERIA, "risk": 72},
            "expected_version": 1,
        },
    )
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["error"]["code"] == "version_conflict"
