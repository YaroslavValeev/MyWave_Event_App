"""Official protocol identity must agree with the roster, including imports."""

import pytest
from sqlalchemy import select

from app.models.athlete import AthleteProfile
from app.models.participant import Participant
from app.models.user import User
from conftest import auth_header


@pytest.mark.parametrize(
    "has_profile,has_user",
    [(True, False), (True, True), (False, True), (False, False)],
)
def test_official_protocol_uses_profile_identity_with_legacy_fallback(
    client, db_session, has_profile, has_user
):
    org = auth_header(client, "identity-organizer@example.com", "organizer")
    created = client.post(
        "/api/v1/events",
        headers=org,
        json={"slug": "identity-cup", "title": "Тест идентичности", "status": "draft"},
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]
    profile = None
    user = None
    if has_profile:
        profile = AthleteProfile(
            athlete_id="MW-PROFILE-TEST", display_name="Тестовый спортсмен"
        )
        db_session.add(profile)
        db_session.flush()
    if has_user:
        auth_header(client, "identity-account@example.com", "participant")
        user = db_session.scalar(
            select(User).where(User.email == "identity-account@example.com")
        )
        user.athlete_id = "MW-ACCOUNT-TEST"
        db_session.add(user)
        db_session.flush()
    participant = Participant(
        event_id=event_id,
        full_name="Тестовый спортсмен",
        status="registered",
        athlete_profile_id=profile.id if profile else None,
        user_id=user.id if user else None,
    )
    db_session.add(participant)
    db_session.commit()
    expected = profile.athlete_id if profile else (user.athlete_id if user else None)
    base = f"/api/v1/events/{event_id}"
    roster = client.get(base + "/participants", headers=org)
    assert roster.status_code == 200
    assert roster.json()["items"][0]["athlete_id"] == expected
    for suffix in ("/official-protocol", "/official-protocol/download"):
        exported = client.get(base + suffix, headers=org)
        assert exported.status_code == 200, exported.text
        item = next(p for p in exported.json()["participants"] if p["id"] == participant.id)
        assert item["athlete_id"] == expected
