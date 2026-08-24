"""Document upload, checklist, heats foundation tests."""

from __future__ import annotations

from io import BytesIO

from conftest import auth_header


def _create_published_event(client, headers, slug: str = "cup-docs"):
    created = client.post(
        "/api/v1/events",
        headers=headers,
        json={"slug": slug, "title": "Cup", "status": "draft"},
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    patched = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers,
        json={"status": "registration_open"},
    )
    assert patched.status_code == 200
    return event_id


def test_document_upload_and_download(client, tmp_path, monkeypatch):
    org = auth_header(client, "doc-org@example.com", "organizer")
    event_id = _create_published_event(client, org, "doc-upload-event")

    from app.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(Settings, "repo_root", property(lambda self: tmp_path))
    get_settings.cache_clear()
    (tmp_path / "data" / "documents").mkdir(parents=True, exist_ok=True)

    pdf = BytesIO(b"%PDF-1.4 test document content")
    upload = client.post(
        f"/api/v1/events/{event_id}/documents",
        headers=org,
        files={"file": ("rules.pdf", pdf, "application/pdf")},
        data={"title": "Правила", "kind": "rules", "language": "ru"},
    )
    assert upload.status_code == 201, upload.text
    doc = upload.json()
    assert doc["title"] == "Правила"
    assert doc["kind"] == "rules"
    assert doc["file_name"] == "rules.pdf"

    listed = client.get(f"/api/v1/events/{event_id}/documents", headers=org)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    downloaded = client.get(
        f"/api/v1/events/{event_id}/documents/{doc['id']}/file",
        headers=org,
    )
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"%PDF")

    part = auth_header(client, "doc-part@example.com", "participant")
    denied = client.post(
        f"/api/v1/events/{event_id}/documents",
        headers=part,
        files={"file": ("x.pdf", BytesIO(b"%PDF-1.4 x"), "application/pdf")},
        data={"title": "X", "kind": "other"},
    )
    assert denied.status_code == 403

    deleted = client.delete(f"/api/v1/events/{event_id}/documents/{doc['id']}", headers=org)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/events/{event_id}/documents", headers=org).json()["total"] == 0


def test_document_rejects_exe(client, tmp_path, monkeypatch):
    org = auth_header(client, "doc-bad@example.com", "organizer")
    event_id = _create_published_event(client, org, "doc-bad-event")
    from app.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(Settings, "repo_root", property(lambda self: tmp_path))
    get_settings.cache_clear()
    (tmp_path / "data" / "documents").mkdir(parents=True, exist_ok=True)

    bad = client.post(
        f"/api/v1/events/{event_id}/documents",
        headers=org,
        files={"file": ("malware.exe", BytesIO(b"MZ"), "application/octet-stream")},
        data={"title": "Nope", "kind": "other"},
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "invalid_file_type"


def test_checklist_ensure_and_toggle(client):
    org = auth_header(client, "check-org@example.com", "organizer")
    event_id = _create_published_event(client, org, "check-event")

    first = client.get(f"/api/v1/events/{event_id}/checklist", headers=org)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["total"] >= 7
    codes = {i["code"] for i in body["items"]}
    assert "documents" in codes
    assert "start_lists" in codes
    # registration_open auto-ticks registration
    reg = next(i for i in body["items"] if i["code"] == "registration")
    assert reg["is_done"] is True

    medical = next(i for i in body["items"] if i["code"] == "medical")
    patched = client.patch(
        f"/api/v1/events/{event_id}/checklist/{medical['id']}",
        headers=org,
        json={"is_done": True},
    )
    assert patched.status_code == 200
    assert patched.json()["is_done"] is True

    part = auth_header(client, "check-part@example.com", "participant")
    denied = client.patch(
        f"/api/v1/events/{event_id}/checklist/{medical['id']}",
        headers=part,
        json={"is_done": False},
    )
    assert denied.status_code == 403


def test_heat_start_list_run_flow(client, db_session):
    from app.models.category import Category
    from app.models.participant import Participant

    org = auth_header(client, "heat-org@example.com", "organizer")
    event_id = _create_published_event(client, org, "heat-event")

    cat = Category(event_id=event_id, code="OPEN", title="Open", discipline="wakeboard")
    db_session.add(cat)
    db_session.flush()
    part = Participant(
        event_id=event_id,
        category_id=cat.id,
        full_name="Test Rider",
        status="accepted",
    )
    db_session.add(part)
    db_session.commit()
    participant_id = part.id
    category_id = cat.id

    heat = client.post(
        f"/api/v1/events/{event_id}/heats",
        headers=org,
        json={
            "code": "Q1",
            "title": "Qualification Heat 1",
            "heat_number": 1,
            "category_id": category_id,
        },
    )
    assert heat.status_code == 201, heat.text
    heat_id = heat.json()["id"]
    assert heat.json()["status"] == "planned"

    entry = client.post(
        f"/api/v1/events/{event_id}/heats/{heat_id}/start-list",
        headers=org,
        json={"participant_id": participant_id, "start_order": 1, "bib_number": "7"},
    )
    assert entry.status_code == 201, entry.text
    entry_id = entry.json()["id"]

    status = client.patch(
        f"/api/v1/events/{event_id}/heats/{heat_id}/start-list/{entry_id}/status",
        headers=org,
        json={"status": "checked_in"},
    )
    assert status.status_code == 200
    assert status.json()["status"] == "checked_in"
    assert status.json()["checked_in_at"] is not None

    on_water = client.patch(
        f"/api/v1/events/{event_id}/heats/{heat_id}/start-list/{entry_id}/status",
        headers=org,
        json={"status": "on_water"},
    )
    assert on_water.status_code == 200
    assert on_water.json()["on_water_at"] is not None

    runs = client.get(f"/api/v1/events/{event_id}/heats/{heat_id}/runs", headers=org)
    assert runs.status_code == 200
    assert runs.json()["total"] == 1
    assert runs.json()["items"][0]["status"] == "on_water"

    heat_ready = client.patch(
        f"/api/v1/events/{event_id}/heats/{heat_id}/status",
        headers=org,
        json={"status": "on_water"},
    )
    assert heat_ready.status_code == 200

    checklist = client.get(f"/api/v1/events/{event_id}/checklist", headers=org)
    start_item = next(i for i in checklist.json()["items"] if i["code"] == "start_lists")
    assert start_item["is_done"] is True


def test_fill_start_list_and_results_lifecycle(client, db_session):
    from app.models.category import Category
    from app.models.participant import Participant

    org = auth_header(client, "fill-org@example.com", "organizer")
    event_id = _create_published_event(client, org, "fill-event")

    cat = Category(event_id=event_id, code="JR", title="Juniors", discipline="wakesurf")
    db_session.add(cat)
    db_session.flush()
    for name in ("Alpha Rider", "Beta Rider"):
        db_session.add(
            Participant(
                event_id=event_id,
                category_id=cat.id,
                full_name=name,
                status="accepted",
            )
        )
    db_session.commit()
    category_id = cat.id

    heat = client.post(
        f"/api/v1/events/{event_id}/heats",
        headers=org,
        json={"code": "F1", "title": "Final", "heat_number": 1, "category_id": category_id},
    )
    heat_id = heat.json()["id"]
    filled = client.post(
        f"/api/v1/events/{event_id}/heats/{heat_id}/start-list/fill",
        headers=org,
        json={"category_id": category_id},
    )
    assert filled.status_code == 201, filled.text
    assert filled.json()["total"] == 2

    parts = client.get(f"/api/v1/events/{event_id}/participants", headers=org).json()["items"]
    pid = parts[0]["id"]
    draft = client.post(
        f"/api/v1/events/{event_id}/results",
        headers=org,
        json={"participant_id": pid, "score": 88.5, "place": 1, "heat_id": heat_id},
    )
    assert draft.status_code == 201, draft.text
    result_id = draft.json()["id"]
    assert draft.json()["status"] == "draft"

    verified = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=org,
        json={"status": "verified"},
    )
    assert verified.status_code == 200
    published = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=org,
        json={"status": "published"},
    )
    assert published.status_code == 200
    assert published.json()["published_at"] is not None

    history = client.get(
        f"/api/v1/events/{event_id}/results/{result_id}/history",
        headers=org,
    )
    assert history.status_code == 200
    assert history.json()["total"] >= 2

    blocked = client.post(
        f"/api/v1/events/{event_id}/results",
        headers=org,
        json={"participant_id": pid, "score": 90, "place": 1, "heat_id": heat_id},
    )
    assert blocked.status_code == 409
