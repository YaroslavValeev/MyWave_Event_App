"""Finalized result evidence stays stable until an authorized reopen."""

import pytest
from sqlalchemy import select

from conftest import auth_header
from app.models.judge_score import JudgeScore
from app.models.result import Result
from test_official_protocol import _create_scored_event


def _context(client, status="published"):
    org, event_id, participant_id = _create_scored_event(client)
    base = f"/api/v1/events/{event_id}"
    result = client.get(base + "/results", headers=org).json()["items"][0]
    chief = auth_header(client, "locked-chief@example.com", "chief_judge")
    if status == "verified":
        assert client.patch(
            base + f"/results/{result['id']}/status", headers=chief,
            json={"status": "void"},
        ).status_code == 200
        for state in ("draft", "verified"):
            assert client.patch(
                base + f"/results/{result['id']}/status", headers=org,
                json={"status": state},
            ).status_code == 200
    return org, chief, base, participant_id, result["id"]


def _sheet(client, base, participant_id, actor, **overrides):
    payload = {
        "participant_id": participant_id, "attempt_no": 1,
        "criteria": dict.fromkeys(
            ("difficulty", "risk", "intensity", "variety", "execution"), 100
        ),
    }
    payload.update(overrides)
    return client.post(base + "/judge-scores", headers=actor, json=payload)


@pytest.mark.parametrize("status", ["verified", "published"])
@pytest.mark.parametrize("actor_kind", ["existing", "new", "chief"])
def test_finalized_panel_rejects_changed_or_added_sheets(client, status, actor_kind):
    org, chief, base, pid, _ = _context(client, status)
    actor = chief if actor_kind == "chief" else auth_header(
        client, "op-j1@example.com" if actor_kind == "existing" else "new-judge@example.com",
        "judge",
    )
    before = client.get(base + "/official-protocol", headers=org).json()
    denied = _sheet(client, base, pid, actor)
    assert denied.status_code == 409, denied.text
    assert denied.json()["error"]["code"] == "immutable"
    after = client.get(base + "/official-protocol", headers=org).json()
    assert after["judge_scores"] == before["judge_scores"]
    assert after["results"] == before["results"]


@pytest.mark.parametrize("status", ["verified", "published"])
def test_authorized_reopen_allows_correction_and_preserves_result_history(client, status):
    org, chief, base, pid, rid = _context(client, status)
    endpoint = base + f"/results/{rid}/status"
    if status == "published":
        assert client.patch(endpoint, headers=org, json={"status": "void"}).status_code == 403
        assert client.patch(endpoint, headers=chief, json={"status": "void"}).status_code == 200
    assert client.patch(endpoint, headers=org, json={"status": "draft"}).status_code == 200
    judge = auth_header(client, "op-j1@example.com", "judge")
    corrected = _sheet(client, base, pid, judge)
    assert corrected.status_code == 201, corrected.text
    aggregated = client.post(base + "/judge-scores/aggregate", headers=org, json={
        "participant_id": pid, "attempt_no": 1, "write_result_draft": True,
    })
    assert aggregated.status_code == 200, aggregated.text
    assert aggregated.json()["panel_score"] == pytest.approx(83.33, abs=0.01)
    assert client.patch(endpoint, headers=org, json={"status": "verified"}).status_code == 200
    assert client.patch(endpoint, headers=chief, json={"status": "published"}).status_code == 200
    result = client.get(base + "/results").json()["items"][0]
    assert result["score"] == pytest.approx(83.33, abs=0.01)
    history = client.get(base + f"/results/{rid}/history", headers=org).json()["items"]
    assert any(row["score"] == 75 for row in history)
    assert any(row["score"] == pytest.approx(83.33, abs=0.01) for row in history)


def test_another_attempt_remains_editable(client):
    org, _, base, pid, _ = _context(client)
    judge = auth_header(client, "op-j1@example.com", "judge")
    response = _sheet(client, base, pid, judge, attempt_no=2)
    assert response.status_code == 201, response.text
    published = client.get(base + "/results").json()["items"][0]
    assert published["score"] == 75
    scores = client.get(base + "/judge-scores", headers=org).json()["items"]
    assert all(row["total"] == 75 for row in scores if row["attempt_no"] == 1)


def test_moving_sheet_cannot_bypass_old_heat_lock(client):
    org, _, base, pid, _ = _context(client)
    heat = client.post(base + "/heats", headers=org, json={
        "code": "NEXT", "title": "Следующий заезд", "heat_number": 2,
    })
    assert heat.status_code == 201, heat.text
    judge = auth_header(client, "op-j1@example.com", "judge")
    response = _sheet(client, base, pid, judge, heat_id=heat.json()["id"])
    assert response.status_code == 409, response.text
    sheets = client.get(base + "/judge-scores", headers=org).json()["items"]
    assert all(row["heat_id"] is None and row["total"] == 75 for row in sheets)


def test_new_unassigned_sheet_cannot_bypass_finalized_heat_scope(client, db_session):
    org, _, base, pid, result_id = _context(client)
    heat_response = client.post(
        base + "/heats",
        headers=org,
        json={"code": "LOCKED", "title": "Заезд с итогом", "heat_number": 2},
    )
    assert heat_response.status_code == 201, heat_response.text
    heat_id = heat_response.json()["id"]

    result = db_session.get(Result, result_id)
    assert result is not None
    result.heat_id = heat_id
    sheets = list(
        db_session.scalars(
            select(JudgeScore).where(
                JudgeScore.event_id == result.event_id,
                JudgeScore.participant_id == pid,
                JudgeScore.attempt_no == result.attempt_no,
            )
        ).all()
    )
    for sheet in sheets:
        sheet.heat_id = heat_id
    db_session.commit()

    new_judge = auth_header(client, "unassigned-heat-judge@example.com", "judge")
    response = _sheet(client, base, pid, new_judge, heat_id=None)

    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "immutable"


def test_unrelated_heat_accepts_new_judge_sheet(client):
    org, _, base, pid, _ = _context(client)
    heat = client.post(base + "/heats", headers=org, json={
        "code": "OTHER", "title": "Другой заезд", "heat_number": 2,
    })
    assert heat.status_code == 201, heat.text
    judge = auth_header(client, "other-heat-judge@example.com", "judge")
    response = _sheet(client, base, pid, judge, heat_id=heat.json()["id"])
    assert response.status_code == 201, response.text
