"""Scan protocol pack: Kazan day-of sheets → heats, start lists, draft results."""

from __future__ import annotations

from sqlalchemy import select

from app.data.kazan_2026_protocol import HEATS, _e, _h, BOAT
from app.models.heat import Heat, StartListEntry
from app.models.official import Official
from app.models.participant import Participant
from app.models.result import Result
from app.services.event_pack_service import _latin_key
from conftest import auth_header


def _event(client, org, slug: str = "scan-kazan") -> int:
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={
            "slug": slug,
            "title": "Чемпионат России в Казани 2026",
            "city": "Казань",
            "status": "draft",
        },
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=org,
        json={"status": "registration_open"},
    )
    return event_id


def test_latin_key_georgiy_alias():
    assert _latin_key("Likhtarev Georgiy") == _latin_key("Likhtarev Georgii")
    assert _latin_key("Solovev Andrei_Jr") == _latin_key("Solovev Andrei Jr")
    assert _latin_key("Kopalkina* Tatiana") == _latin_key("Kopalkina Tatiana")


def test_scan_protocol_applies_draft_results(client, db_session):
    org = auth_header(client, "scan-org@example.com", "organizer")
    event_id = _event(client, org)

    response = client.post(f"/api/v1/events/{event_id}/scan-protocol", headers=org)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["heats"] == len(HEATS)
    assert body["entries"] == sum(len(h["entries"]) for h in HEATS)
    assert body["results"] > 0
    assert body["dns"] >= 2

    heats = list(db_session.scalars(select(Heat).where(Heat.event_id == event_id)).all())
    assert len(heats) == len(HEATS)
    assert any("квалификация" in h.title for h in heats)
    assert any("полуфинал" in h.title for h in heats)
    assert any("финал" in h.title for h in heats)

    results = list(db_session.scalars(select(Result).where(Result.event_id == event_id)).all())
    assert results
    assert all(r.status == "draft" for r in results)
    assert any(r.score == 53.33 for r in results)
    assert any(r.score == 80.56 for r in results)

    parts = list(db_session.scalars(select(Participant).where(Participant.event_id == event_id)).all())
    likhtarev = [
        p
        for p in parts
        if "Likhtarev" in (p.full_name or "") or "Лихтар" in (p.full_name or "")
    ]
    assert len(likhtarev) == 1

    entries = list(db_session.scalars(select(StartListEntry).where(StartListEntry.event_id == event_id)).all())
    assert any(e.status == "dns" and e.notes and "Fursova" in e.notes for e in entries)
    assert any(e.status == "dns" and e.notes and "Kostenko" in e.notes for e in entries)

    officials = list(db_session.scalars(select(Official).where(Official.event_id == event_id)).all())
    assert any("Balakin" in o.full_name for o in officials)

    from app.models.category import Category
    from app.models.event import Event

    event = db_session.get(Event, event_id)
    assert event is not None
    assert "Нижний Кабан" in (event.venue or "")
    codes = {
        c.code for c in db_session.scalars(select(Category).where(Category.event_id == event_id)).all()
    }
    assert "wb-o30-m" in codes
    assert "ws-o30-f" in codes
    assert "wb-o40-m" in codes
    chernov_ids = {
        p.id for p in parts if "Chernov" in (p.full_name or "") or "Чернов" in (p.full_name or "")
    }
    assert chernov_ids
    assert any(r.participant_id in chernov_ids and r.place == 1 for r in results)
    terekhova = [p for p in parts if "Terekhova" in (p.full_name or "") or "Терехова" in (p.full_name or "")]
    assert len(terekhova) >= 2
    filippova = next(p for p in parts if "Filippova" in (p.full_name or "") or "Филиппова" in (p.full_name or ""))
    assert any(r.participant_id == filippova.id and r.place == 1 for r in results)
    semenov = next(p for p in parts if "Semenov" in (p.full_name or "") or "Семенов" in (p.full_name or ""))
    assert any(r.participant_id == semenov.id and r.place == 1 for r in results)

    guest = client.get(f"/api/v1/events/{event_id}/results")
    assert guest.status_code == 200, guest.text
    assert guest.json()["total"] == 0

    again = client.post(f"/api/v1/events/{event_id}/scan-protocol", headers=org)
    assert again.status_code == 200, again.text
    assert again.json()["heats"] == body["heats"]
    assert again.json()["entries"] == body["entries"]
    db_session.expire_all()
    heats2 = list(db_session.scalars(select(Heat).where(Heat.event_id == event_id)).all())
    assert len(heats2) == len(HEATS)
    results2 = list(db_session.scalars(select(Result).where(Result.event_id == event_id)).all())
    assert all(r.status == "draft" for r in results2)


def test_scan_protocol_forbidden_for_participant(client):
    org = auth_header(client, "scan-org2@example.com", "organizer")
    event_id = _event(client, org, slug="scan-kazan-part")
    participant = auth_header(client, "scan-athlete@example.com", "participant")
    response = client.post(f"/api/v1/events/{event_id}/scan-protocol", headers=participant)
    assert response.status_code == 403


def test_scan_protocol_synthetic_subset(client, db_session):
    from app.services.protocol_pack_service import apply_scan_protocol
    from app.models.user import User

    org = auth_header(client, "scan-mini@example.com", "organizer")
    event_id = _event(client, org, slug="scan-mini")
    actor = db_session.scalar(select(User).where(User.email == "scan-mini@example.com"))
    assert actor is not None
    mini = [
        _h(
            "mini-wb-open-f-qual1",
            disc="Wakeboard (boat)",
            klass="Open",
            sex="f",
            rnd="qual",
            idx=1,
            when="2026-08-13T13:00:00+03:00",
            engine=BOAT,
            entries=[
                _e(1, "Shupliakova Anastasia", place=1, score=37.78, q="Q", seeded=True, execution=12.21),
                _e(2, "Petrova Valentina", place=3, score=20.67, q="L"),
            ],
        )
    ]
    out = apply_scan_protocol(db_session, event_id=event_id, actor=actor, heats=mini, audit_enabled=False)
    assert out["heats"] == 1
    assert out["entries"] == 2
    assert out["results"] == 2
    db_session.expire_all()
    res = list(db_session.scalars(select(Result).where(Result.event_id == event_id)).all())
    assert len(res) == 2
    assert all(r.status == "draft" for r in res)
    assert any(r.score == 37.78 and r.place == 1 for r in res)
