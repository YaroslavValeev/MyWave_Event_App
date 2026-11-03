"""Native PDF/DOCX protocol export."""

from __future__ import annotations

from conftest import auth_header


def _seed_ready_event(client, slug: str = "doc-cup"):
    org = auth_header(client, f"{slug}-org@example.com", "organizer")
    event_id = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": slug, "title": "Document Cup", "status": "draft"},
    ).json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "registration_open"},
    )
    client.put(
        f"/api/v1/events/{event_id}/rules-profile",
        headers=org,
        json={
            "governing_body": "FVLS",
            "sanction_body": "IWWF",
            "discipline_codes": ["wakeskim"],
            "scoring_mode": "manual",
        },
    )
    part = auth_header(client, f"{slug}-ath@example.com", "participant")
    pid = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=part,
        json={"category_id": None},
    ).json()["id"]
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
    rid = client.post(
        f"/api/v1/events/{event_id}/results",
        headers=org,
        json={"participant_id": pid, "score": 91.5, "place": 1},
    ).json()["id"]
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
    return event_id, org


def test_live_pdf_and_docx(client):
    event_id, org = _seed_ready_event(client, "live-docs")
    pdf = client.get(f"/api/v1/events/{event_id}/official-protocol/pdf", headers=org)
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content[:4] == b"%PDF"

    docx = client.get(f"/api/v1/events/{event_id}/official-protocol/docx", headers=org)
    assert docx.status_code == 200, docx.text
    assert docx.content[:2] == b"PK"


def test_revision_pdf_docx(client):
    event_id, org = _seed_ready_event(client, "rev-docs")
    created = client.post(
        f"/api/v1/events/{event_id}/official-protocol/revisions",
        headers=org,
        json={"note": "День 1"},
    )
    assert created.status_code == 201, created.text
    rev_id = created.json()["id"]

    pdf = client.get(
        f"/api/v1/events/{event_id}/official-protocol/revisions/{rev_id}/pdf",
        headers=org,
    )
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"

    docx = client.get(
        f"/api/v1/events/{event_id}/official-protocol/revisions/{rev_id}/docx",
        headers=org,
    )
    assert docx.status_code == 200
    assert docx.content[:2] == b"PK"
