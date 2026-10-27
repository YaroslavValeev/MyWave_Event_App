"""P0 vertical slice: roster lock + chief judge publish gate."""

from __future__ import annotations

from conftest import auth_header, register_payload


def test_roster_lock_blocks_new_accept_and_allows_checkin(client, db_session):
    from app.models.category import Category

    org = auth_header(client, "p0-lock-org@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "p0-lock-cup", "title": "P0 Lock Cup", "status": "registration_open"},
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    assert created.json().get("roster_locked_at") is None

    empty = client.post(f"/api/v1/events/{event_id}/roster/lock", headers=org, json={})
    assert empty.status_code == 400
    assert empty.json()["error"]["code"] == "roster_empty"

    cat = Category(event_id=event_id, code="OPEN", title="Open", discipline="wakesurf")
    db_session.add(cat)
    db_session.commit()

    reg = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79007771001",
            email="p0.lock.athlete@example.com",
            display_name="Атлет Лок",
        ),
    )
    athlete = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    app = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=athlete,
        json={"category_id": cat.id},
    )
    assert app.status_code == 201, app.text
    app_id = app.json()["id"]
    accepted = client.patch(
        f"/api/v1/events/{event_id}/applications/{app_id}",
        headers=org,
        json={"status": "accepted"},
    )
    assert accepted.status_code == 200

    locked = client.post(
        f"/api/v1/events/{event_id}/roster/lock",
        headers=org,
        json={"reason": "стартовый протокол готов"},
    )
    assert locked.status_code == 200, locked.text
    assert locked.json()["roster_locked_at"] is not None

    again = client.post(f"/api/v1/events/{event_id}/roster/lock", headers=org, json={})
    assert again.status_code == 200

    judge = auth_header(client, "p0-lock-judge@example.com", "judge")
    forbidden = client.post(f"/api/v1/events/{event_id}/roster/lock", headers=judge, json={})
    assert forbidden.status_code == 403

    second = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79007771002",
            email="p0.lock.late@example.com",
            display_name="Поздний Атлет",
        ),
    )
    late = {"Authorization": f"Bearer {second.json()['access_token']}"}
    blocked_app = client.post(
        f"/api/v1/events/{event_id}/applications",
        headers=late,
        json={"category_id": cat.id},
    )
    assert blocked_app.status_code == 409
    assert blocked_app.json()["error"]["code"] == "roster_locked"

    heat = client.post(
        f"/api/v1/events/{event_id}/heats",
        headers=org,
        json={"code": "Q1", "title": "Qual", "heat_number": 1, "category_id": cat.id},
    )
    assert heat.status_code == 201, heat.text
    heat_id = heat.json()["id"]
    filled = client.post(
        f"/api/v1/events/{event_id}/heats/{heat_id}/start-list/fill",
        headers=org,
        json={"category_id": cat.id},
    )
    assert filled.status_code == 201, filled.text
    entry_id = filled.json()["items"][0]["id"]
    checkin = client.patch(
        f"/api/v1/events/{event_id}/heats/{heat_id}/start-list/{entry_id}/status",
        headers=org,
        json={"status": "checked_in"},
    )
    assert checkin.status_code == 200
    assert checkin.json()["status"] == "checked_in"

    unlocked = client.post(
        f"/api/v1/events/{event_id}/roster/unlock",
        headers=org,
        json={"reason": "добавить опоздавшего"},
    )
    assert unlocked.status_code == 200
    assert unlocked.json()["roster_locked_at"] is None


def test_organizer_cannot_publish_without_chief_judge(client, db_session):
    from app.models.category import Category
    from app.models.participant import Participant

    org = auth_header(client, "p0-pub-org@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "p0-publish-cup", "title": "P0 Publish Cup", "status": "published"},
    )
    event_id = created.json()["id"]
    cat = Category(event_id=event_id, code="OPEN", title="Open", discipline="wakesurf")
    db_session.add(cat)
    db_session.flush()
    part = Participant(event_id=event_id, category_id=cat.id, full_name="Rider One", status="accepted")
    db_session.add(part)
    db_session.commit()

    draft = client.post(
        f"/api/v1/events/{event_id}/results",
        headers=org,
        json={"participant_id": part.id, "score": 77.1, "place": 1},
    )
    assert draft.status_code == 201, draft.text
    result_id = draft.json()["id"]

    verified = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=org,
        json={"status": "verified"},
    )
    assert verified.status_code == 200

    judge = auth_header(client, "p0-pub-judge@example.com", "judge")
    judge_pub = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=judge,
        json={"status": "published"},
    )
    assert judge_pub.status_code == 403

    org_pub = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=org,
        json={"status": "published"},
    )
    assert org_pub.status_code == 403
    assert org_pub.json()["error"]["code"] == "chief_approval_required"

    guest_results = client.get(f"/api/v1/events/{event_id}/results")
    assert guest_results.status_code == 200
    assert guest_results.json()["total"] == 0

    chief = auth_header(client, "p0-pub-chief@example.com", "chief_judge")
    published = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=chief,
        json={"status": "published"},
    )
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "published"

    guest_after = client.get(f"/api/v1/events/{event_id}/results")
    assert guest_after.json()["total"] == 1
    assert guest_after.json()["items"][0]["status"] == "published"

    org_void = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=org,
        json={"status": "void"},
    )
    assert org_void.status_code == 403

    archived = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "completed"},
    )
    assert archived.status_code == 200
    blocked_lock = client.post(f"/api/v1/events/{event_id}/roster/lock", headers=org, json={})
    assert blocked_lock.status_code == 409
    assert blocked_lock.json()["error"]["code"] == "event_archived"


def test_participant_cannot_lock_roster_or_publish(client, db_session):
    from app.models.category import Category
    from app.models.participant import Participant

    org = auth_header(client, "p0-authz-org@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "p0-authz-cup", "title": "P0 Authz Cup", "status": "published"},
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    cat = Category(event_id=event_id, code="OPEN", title="Open", discipline="wakesurf")
    db_session.add(cat)
    db_session.flush()
    part = Participant(event_id=event_id, category_id=cat.id, full_name="Rider Authz", status="accepted")
    db_session.add(part)
    db_session.commit()

    athlete = auth_header(client, "p0-authz-athlete@example.com", "participant")
    lock = client.post(f"/api/v1/events/{event_id}/roster/lock", headers=athlete, json={})
    assert lock.status_code == 403
    unlock = client.post(f"/api/v1/events/{event_id}/roster/unlock", headers=athlete, json={})
    assert unlock.status_code == 403

    draft = client.post(
        f"/api/v1/events/{event_id}/results",
        headers=org,
        json={"participant_id": part.id, "score": 50, "place": 1},
    )
    assert draft.status_code == 201, draft.text
    result_id = draft.json()["id"]
    verified = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=org,
        json={"status": "verified"},
    )
    assert verified.status_code == 200
    athlete_pub = client.patch(
        f"/api/v1/events/{event_id}/results/{result_id}/status",
        headers=athlete,
        json={"status": "published"},
    )
    assert athlete_pub.status_code == 403

