"""Field moments camera capture tests."""

from __future__ import annotations

from io import BytesIO

from conftest import auth_header


def _event(client, headers, slug: str = "moments-cup") -> int:
    created = client.post(
        "/api/v1/events",
        headers=headers,
        json={"slug": slug, "title": "Moments Cup", "status": "draft"},
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers,
        json={"status": "registration_open"},
    )
    return event_id


def test_media_can_upload_photo_participant_forbidden(client, tmp_path, monkeypatch):
    org = auth_header(client, "mom-org@example.com", "organizer")
    media = auth_header(client, "mom-media@example.com", "media")
    event_id = _event(client, org, "mom-photo")

    from app.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(Settings, "repo_root", property(lambda self: tmp_path))
    get_settings.cache_clear()
    (tmp_path / "data" / "field-media").mkdir(parents=True, exist_ok=True)

    png = BytesIO(b"\x89PNG\r\n\x1a\nfake png moment")
    upload = client.post(
        f"/api/v1/events/{event_id}/field-moments",
        headers=media,
        files={"file": ("dock.png", png, "image/png")},
        data={"title": "", "pov": "start_marshal"},
    )
    assert upload.status_code == 201, upload.text
    body = upload.json()
    assert body["pov"] == "start_marshal"
    assert body["media_kind"] == "photo"
    assert body["status"] == "draft"
    assert body["title"] == "Маршал на старте"

    listed = client.get(f"/api/v1/events/{event_id}/field-moments", headers=org)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    downloaded = client.get(
        f"/api/v1/events/{event_id}/field-moments/{body['id']}/file",
        headers=media,
    )
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"\x89PNG")

    part = auth_header(client, "mom-part@example.com", "participant")
    denied = client.post(
        f"/api/v1/events/{event_id}/field-moments",
        headers=part,
        files={"file": ("x.png", BytesIO(b"\x89PNG"), "image/png")},
        data={"title": "X", "pov": "backstage"},
    )
    assert denied.status_code == 403
    listed_part = client.get(f"/api/v1/events/{event_id}/field-moments", headers=part)
    assert listed_part.status_code == 403


def test_field_moment_video_and_status_gate(client, tmp_path, monkeypatch):
    org = auth_header(client, "mom-vid-org@example.com", "organizer")
    support = auth_header(client, "mom-marshal@example.com", "support")
    event_id = _event(client, org, "mom-video")

    from app.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(Settings, "repo_root", property(lambda self: tmp_path))
    get_settings.cache_clear()
    (tmp_path / "data" / "field-media").mkdir(parents=True, exist_ok=True)

    video = client.post(
        f"/api/v1/events/{event_id}/field-moments",
        headers=support,
        files={"file": ("pilot.mp4", BytesIO(b"ftypisom fake mp4"), "video/mp4")},
        data={"title": "С катера", "pov": "boat_pilot"},
    )
    assert video.status_code == 201, video.text
    assert video.json()["media_kind"] == "video"
    moment_id = video.json()["id"]

    denied = client.patch(
        f"/api/v1/events/{event_id}/field-moments/{moment_id}",
        headers=support,
        json={"status": "approved"},
    )
    assert denied.status_code == 403

    approved = client.patch(
        f"/api/v1/events/{event_id}/field-moments/{moment_id}",
        headers=org,
        json={"status": "approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    exe = client.post(
        f"/api/v1/events/{event_id}/field-moments",
        headers=org,
        files={"file": ("x.exe", BytesIO(b"MZ"), "application/octet-stream")},
        data={"title": "Nope", "pov": "other"},
    )
    assert exe.status_code == 400
    assert exe.json()["error"]["code"] == "invalid_file_type"


def test_commentator_upload_guest_and_invalid_pov(client, tmp_path, monkeypatch):
    org = auth_header(client, "mom-comm-org@example.com", "organizer")
    commentator = auth_header(client, "mom-comm@example.com", "commentator")
    event_id = _event(client, org, "mom-comm")

    from app.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(Settings, "repo_root", property(lambda self: tmp_path))
    get_settings.cache_clear()
    (tmp_path / "data" / "field-media").mkdir(parents=True, exist_ok=True)

    upload = client.post(
        f"/api/v1/events/{event_id}/field-moments",
        headers=commentator,
        files={"file": ("crowd.webp", BytesIO(b"RIFF....WEBP"), "image/webp")},
        data={"title": "", "pov": "crowd"},
    )
    assert upload.status_code == 201, upload.text
    assert upload.json()["pov"] == "crowd"
    assert upload.json()["title"] == "Зрители и эмоции"

    guest = client.get(f"/api/v1/events/{event_id}/field-moments")
    assert guest.status_code == 401

    bad_pov = client.post(
        f"/api/v1/events/{event_id}/field-moments",
        headers=commentator,
        files={"file": ("x.png", BytesIO(b"\x89PNG"), "image/png")},
        data={"title": "X", "pov": "instagram"},
    )
    assert bad_pov.status_code == 400
    assert bad_pov.json()["error"]["code"] == "invalid_pov"
