"""Event publications API — ADR-0013."""

from __future__ import annotations

import io

from conftest import auth_header


def _png_bytes() -> bytes:
    # Minimal 1x1 PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _seed_live_event(client, slug: str = "pub-cup"):
    org = auth_header(client, f"{slug}-org@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": slug, "title": "Publication Cup", "status": "draft"},
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "live"},
    )
    return event_id, org


def test_organizer_publishes_news_direct(client):
    event_id, org = _seed_live_event(client, "news-direct")
    resp = client.post(
        f"/api/v1/events/{event_id}/publications",
        headers={**org, "Idempotency-Key": "news-1"},
        json={
            "type": "news",
            "title": "День 1 завершён",
            "body": "Результаты опубликованы.",
            "author_role": "organizer",
            "intent": "publish",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "published"
    assert body["type"] == "news"
    assert body["author_role"] == "organizer"

    guest = client.get(f"/api/v1/events/{event_id}/publications")
    assert guest.status_code == 200
    assert guest.json()["total"] == 1


def test_media_post_goes_to_moderation(client):
    event_id, org = _seed_live_event(client, "media-mod")
    media = auth_header(client, "media-mod@media.example", "media")
    resp = client.post(
        f"/api/v1/events/{event_id}/publications",
        headers=media,
        json={
            "type": "post",
            "title": "Фото с воды",
            "body": "Кадр с финиша",
            "author_role": "media",
            "intent": "publish",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "pending_moderation"

    guest = client.get(f"/api/v1/events/{event_id}/publications")
    assert guest.json()["total"] == 0

    pub_id = resp.json()["id"]
    approved = client.post(
        f"/api/v1/events/{event_id}/publications/{pub_id}/moderate",
        headers=org,
        json={"action": "publish"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "published"
    assert client.get(f"/api/v1/events/{event_id}/publications").json()["total"] == 1


def test_author_role_mismatch_forbidden(client):
    event_id, _org = _seed_live_event(client, "role-mismatch")
    media = auth_header(client, "mismatch@media.example", "media")
    resp = client.post(
        f"/api/v1/events/{event_id}/publications",
        headers=media,
        json={
            "type": "post",
            "title": "Hack",
            "body": "x",
            "author_role": "organizer",
            "intent": "publish",
        },
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "author_role_mismatch"


def test_participant_cannot_create(client):
    event_id, _org = _seed_live_event(client, "part-deny")
    part = auth_header(client, "part@example.com", "participant")
    resp = client.post(
        f"/api/v1/events/{event_id}/publications",
        headers=part,
        json={
            "type": "post",
            "title": "Nope",
            "body": "x",
            "author_role": "participant",
            "intent": "draft",
        },
    )
    assert resp.status_code == 403


def test_media_cannot_create_news(client):
    event_id, _org = _seed_live_event(client, "news-deny")
    media = auth_header(client, "newsdeny@media.example", "media")
    resp = client.post(
        f"/api/v1/events/{event_id}/publications",
        headers=media,
        json={
            "type": "news",
            "title": "Official?",
            "body": "no",
            "author_role": "media",
            "intent": "draft",
        },
    )
    assert resp.status_code == 403


def test_idempotency_prevents_duplicate(client):
    event_id, org = _seed_live_event(client, "idem")
    payload = {
        "type": "news",
        "title": "Once",
        "body": "only",
        "author_role": "organizer",
        "intent": "publish",
        "idempotency_key": "same-key",
    }
    first = client.post(f"/api/v1/events/{event_id}/publications", headers=org, json=payload)
    second = client.post(f"/api/v1/events/{event_id}/publications", headers=org, json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert client.get(f"/api/v1/events/{event_id}/publications").json()["total"] == 1


def test_upload_image_and_reject_exe(client):
    event_id, org = _seed_live_event(client, "media-up")
    created = client.post(
        f"/api/v1/events/{event_id}/publications",
        headers=org,
        json={
            "type": "post",
            "title": "С фото",
            "body": "тест",
            "author_role": "organizer",
            "intent": "draft",
        },
    )
    assert created.status_code == 201
    pub_id = created.json()["id"]

    ok = client.post(
        f"/api/v1/events/{event_id}/publications/{pub_id}/media",
        headers=org,
        files={"file": ("shot.png", io.BytesIO(_png_bytes()), "image/png")},
    )
    assert ok.status_code == 201, ok.text
    assert len(ok.json()["media"]) == 1

    bad = client.post(
        f"/api/v1/events/{event_id}/publications/{pub_id}/media",
        headers=org,
        files={"file": ("evil.exe", io.BytesIO(b"MZ" + b"\x00" * 20), "application/octet-stream")},
    )
    assert bad.status_code == 400


def test_author_roles_endpoint(client):
    event_id, org = _seed_live_event(client, "roles-ep")
    resp = client.get(f"/api/v1/events/{event_id}/publications/author-roles", headers=org)
    assert resp.status_code == 200
    assert resp.json()["roles"] == ["organizer"]
