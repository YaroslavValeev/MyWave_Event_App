"""Scoring engines and judge score API tests."""

from __future__ import annotations

from conftest import auth_header
from app.domain.scoring_engines import aggregate_panel, judge_sheet_total


def test_wsws_drive_sheet_total():
    total = judge_sheet_total(
        "WSWS_DRIVE",
        {
            "difficulty": 80,
            "risk": 70,
            "intensity": 75,
            "variety": 60,
            "execution": 90,
        },
    )
    assert total == 75.0


def test_aggregate_drop_extremes():
    panel = aggregate_panel("WSWS_DRIVE", [50, 60, 70, 80, 90], drop_extremes=True)
    assert panel["panel_score"] == 70.0
    assert panel["dropped_totals"] == [50.0, 90.0]


def test_judge_score_submit_and_aggregate(client):
    org = auth_header(client, "score-org@example.com", "organizer")
    j1 = auth_header(client, "score-j1@example.com", "judge")
    j2 = auth_header(client, "score-j2@example.com", "judge")
    j3 = auth_header(client, "score-j3@example.com", "judge")

    created = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": "score-drive-cup",
            "title": "DRIVE Cup",
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

    engine = client.get(f"/api/v1/events/{event_id}/scoring/engine", headers=org)
    assert engine.status_code == 200
    assert engine.json()["engine"] == "WSWS_DRIVE"
    assert "difficulty" in engine.json()["criteria"]

    # Seed one participant via application flow is heavy — insert via organizer path:
    # create application as participant then accept.
    part_user = auth_header(client, "score-athlete@example.com", "participant")
    # Need category — create none; application with category_id null
    app = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=part_user,
        json={"category_id": None, "region": "Москва"},
    )
    assert app.status_code == 201, app.text
    participant_id = app.json()["id"]
    decided = client.patch(
        f"/api/v1/events/{event_id}/applications/{participant_id}",
        headers=org,
        json={"status": "accepted"},
    )
    assert decided.status_code == 200

    criteria = {
        "difficulty": 80,
        "risk": 70,
        "intensity": 75,
        "variety": 65,
        "execution": 85,
    }
    for headers in (j1, j2, j3):
        posted = client.post(
            f"/api/v1/events/{event_id}/judge-scores",
            headers=headers,
            json={"participant_id": participant_id, "attempt_no": 1, "criteria": criteria},
        )
        assert posted.status_code == 201, posted.text
        assert posted.json()["total"] == 75.0

    listed = client.get(
        f"/api/v1/events/{event_id}/judge-scores",
        headers=org,
        params={"participant_id": participant_id},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 3

    agg = client.post(
        f"/api/v1/events/{event_id}/judge-scores/aggregate",
        headers=org,
        json={"participant_id": participant_id, "attempt_no": 1, "write_result_draft": True},
    )
    assert agg.status_code == 200, agg.text
    body = agg.json()
    assert body["panel_score"] == 75.0
    assert body["judge_count"] == 3
    assert body["result_id"] is not None

    results = client.get(f"/api/v1/events/{event_id}/results", headers=org)
    assert results.status_code == 200
    assert results.json()["items"][0]["score"] == 75.0
