"""Official protocol export tests."""

from __future__ import annotations

from conftest import auth_header


def _create_scored_event(client):
    org = auth_header(client, "op-export@example.com", "organizer")
    j1 = auth_header(client, "op-j1@example.com", "judge")
    j2 = auth_header(client, "op-j2@example.com", "judge")
    j3 = auth_header(client, "op-j3@example.com", "judge")
    part_user = auth_header(client, "op-athlete@example.com", "participant")

    created = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": "export-cup",
            "title": "Export Cup",
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

    app = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=part_user,
        json={"category_id": None, "region": "Казань"},
    )
    assert app.status_code == 201, app.text
    participant_id = app.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/applications/{participant_id}",
        headers=org,
        json={"status": "accepted"},
    )

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

    agg = client.post(
        f"/api/v1/events/{event_id}/judge-scores/aggregate",
        headers=org,
        json={"participant_id": participant_id, "attempt_no": 1, "write_result_draft": True},
    )
    assert agg.status_code == 200, agg.text
    result_id = agg.json()["result_id"]

    verified = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=org,
        json={"status": "verified"},
    )
    assert verified.status_code == 200
    denied = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=org,
        json={"status": "published"},
    )
    assert denied.status_code == 403
    chief = auth_header(client, "op-chief@example.com", "chief_judge")
    published = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=chief,
        json={"status": "published"},
    )
    assert published.status_code == 200

    return org, event_id, participant_id


def test_official_protocol_export_json(client):
    org, event_id, participant_id = _create_scored_event(client)

    preview = client.get(f"/api/v1/events/{event_id}/official-protocol", headers=org)
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["format_version"] == "1.0"
    assert body["event"]["slug"] == "export-cup"
    assert body["rules_profile"]["governing_body"] == "FVLS"
    assert body["scoring_engine"] == "WSWS_DRIVE"
    assert body["readiness"]["official_ready"] is True
    assert body["readiness"]["published_results_count"] == 1
    assert any(r["participant_id"] == participant_id for r in body["results"])
    assert len(body["judge_scores"]) == 3

    denied = client.get(f"/api/v1/events/{event_id}/official-protocol", headers=auth_header(client, "op-part@example.com", "participant"))
    assert denied.status_code == 403


def test_official_protocol_download_and_html(client):
    org, event_id, _ = _create_scored_event(client)

    downloaded = client.get(
        f"/api/v1/events/{event_id}/official-protocol/download",
        headers=org,
    )
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("application/json")
    assert "attachment" in downloaded.headers.get("content-disposition", "")
    assert b"export-cup" in downloaded.content

    html = client.get(
        f"/api/v1/events/{event_id}/official-protocol/html",
        headers=org,
    )
    assert html.status_code == 200
    assert html.headers["content-type"].startswith("text/html")
    assert b"Export Cup" in html.content
    assert b"WSWS_DRIVE" in html.content or b"structured" in html.content


def test_official_protocol_not_ready_without_publish(client):
    org = auth_header(client, "op-draft@example.com", "organizer")
    event_id = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": "draft-only",
            "title": "Draft Only",
            "status": "draft",
            "rules_profile": {
                "governing_body": "FVLS",
                "sanction_body": "IWWF",
                "discipline_codes": ["wakesurf_boat"],
                "scoring_mode": "manual",
            },
        },
    ).json()["id"]

    preview = client.get(f"/api/v1/events/{event_id}/official-protocol", headers=org)
    assert preview.status_code == 200
    readiness = preview.json()["readiness"]
    assert readiness["official_ready"] is False
    assert "no_published_results_or_protocol_captures" in readiness["blockers"]
