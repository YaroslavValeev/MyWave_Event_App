"""Rules catalog and event rules profile tests."""

from __future__ import annotations

from io import BytesIO

from conftest import auth_header


def test_rules_catalog_public(client):
    response = client.get("/api/v1/rules/catalog")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["defaults"]["governing_body"] == "FVLS"
    assert "wakeboard_cable" in data["disciplines"]
    assert "WSWS_WAKESURF_DRIVE" in data["rules_packs"]


def test_event_create_with_rules_profile(client):
    org = auth_header(client, "rules-org@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": "fvls-cup-rules",
            "title": "FVLS Cup",
            "status": "draft",
            "rules_profile": {
                "governing_body": "FVLS",
                "sanction_body": "IWWF",
                "discipline_codes": ["wakeboard_cable", "wakesurf_boat"],
                "scoring_mode": "photo_protocol",
            },
        },
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    assert created.json().get("disciplines")

    profile = client.get(f"/api/v1/events/{event_id}/rules-profile", headers=org)
    assert profile.status_code == 200
    body = profile.json()
    assert body["governing_body"] == "FVLS"
    assert body["sanction_body"] == "IWWF"
    assert set(body["discipline_codes"]) == {"wakeboard_cable", "wakesurf_boat"}
    assert body["rules_packs"]["wakesurf_boat"] == "WSWS_WAKESURF_DRIVE"
    assert body["scoring_mode"] == "photo_protocol"


def test_rules_profile_upsert(client):
    org = auth_header(client, "rules-upsert@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "rules-upsert", "title": "Upsert", "status": "draft"},
    )
    event_id = created.json()["id"]

    missing = client.get(f"/api/v1/events/{event_id}/rules-profile", headers=org)
    assert missing.status_code == 200
    assert missing.json() is None

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
    assert put.json()["discipline_codes"] == ["wakeskim"]
    assert put.json()["scoring_mode"] == "manual"


def test_protocol_upload_verify_and_download(client, tmp_path, monkeypatch):
    org = auth_header(client, "proto-org@example.com", "organizer")
    judge = auth_header(client, "proto-judge@example.com", "judge")
    event_id = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "proto-event", "title": "Proto Cup", "status": "draft"},
    ).json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "registration_open"},
    )

    from app.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(Settings, "repo_root", property(lambda self: tmp_path))
    get_settings.cache_clear()
    (tmp_path / "data" / "protocols").mkdir(parents=True, exist_ok=True)

    png = BytesIO(b"\x89PNG\r\n\x1a\nfake png content")
    upload = client.post(
        f"/api/v1/events/{event_id}/protocol-captures",
        headers=judge,
        files={"file": ("sheet.png", png, "image/png")},
        data={"title": "Лист судьи A", "kind": "judge_sheet", "notes": "Heat 1"},
    )
    assert upload.status_code == 201, upload.text
    capture = upload.json()
    assert capture["status"] == "draft"
    assert capture["kind"] == "judge_sheet"

    listed = client.get(f"/api/v1/events/{event_id}/protocol-captures", headers=org)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    denied_verify = client.patch(
        f"/api/v1/events/{event_id}/protocol-captures/{capture['id']}",
        headers=judge,
        json={"status": "verified"},
    )
    assert denied_verify.status_code == 403

    verified = client.patch(
        f"/api/v1/events/{event_id}/protocol-captures/{capture['id']}",
        headers=org,
        json={"status": "verified", "extracted": {"drive_total": 87.5}},
    )
    assert verified.status_code == 200
    assert verified.json()["status"] == "verified"
    assert verified.json()["extracted"]["drive_total"] == 87.5

    downloaded = client.get(
        f"/api/v1/events/{event_id}/protocol-captures/{capture['id']}/file",
        headers=org,
    )
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"\x89PNG")

    part = auth_header(client, "proto-part@example.com", "participant")
    denied = client.post(
        f"/api/v1/events/{event_id}/protocol-captures",
        headers=part,
        files={"file": ("x.png", BytesIO(b"\x89PNG"), "image/png")},
        data={"title": "X", "kind": "judge_sheet"},
    )
    assert denied.status_code == 403


def test_protocol_rejects_exe(client, tmp_path, monkeypatch):
    org = auth_header(client, "proto-bad@example.com", "organizer")
    event_id = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "proto-bad", "title": "Bad", "status": "draft"},
    ).json()["id"]

    from app.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(Settings, "repo_root", property(lambda self: tmp_path))
    get_settings.cache_clear()
    (tmp_path / "data" / "protocols").mkdir(parents=True, exist_ok=True)

    bad = client.post(
        f"/api/v1/events/{event_id}/protocol-captures",
        headers=org,
        files={"file": ("bad.exe", BytesIO(b"MZ"), "application/octet-stream")},
        data={"title": "Nope", "kind": "judge_sheet"},
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "invalid_file_type"
