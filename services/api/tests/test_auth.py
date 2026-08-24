"""Auth endpoint tests."""

from __future__ import annotations

import os

from sqlalchemy import select

from app.models.auth_extra import RoleApproval
from conftest import auth_header, register_payload


def test_dev_login_and_me(client):
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"email": "organizer@example.com", "role": "organizer"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["role"] == "organizer"
    assert body["email"] == "organizer@example.com"

    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    me_body = me.json()
    assert me_body["email"] == "organizer@example.com"
    assert me_body["role"] == "organizer"
    assert me_body["id"] == body["user_id"]


def test_me_requires_auth(client):
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_dev_login_forbidden_in_production(client):
    from app.config import get_settings

    get_settings.cache_clear()
    os.environ["APP_ENV"] = "production"
    get_settings.cache_clear()

    try:
        response = client.post(
            "/api/v1/auth/dev-login",
            json={"email": "x@example.com", "role": "participant"},
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "dev_login_forbidden"
    finally:
        os.environ["APP_ENV"] = "test"
        get_settings.cache_clear()


def test_roles_accepted(client):
    roles = [
        "participant",
        "organizer",
        "judge",
        "commentator",
        "media",
        "support",
        "federation_manager",
        "event_admin",
        "platform_admin",
    ]
    for role in roles:
        headers = auth_header(client, f"{role}@example.com", role)
        me = client.get("/api/v1/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["role"] == role


def test_register_participant_auto_active(client):
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["role"] == "participant"
    assert body["access_token"]


def test_register_judge_pending_and_approve(client, db_session):
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="89001234567",
            email="judge.pending@example.com",
            display_name="Судья Кандидат",
            requested_role="judge",
        ),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["access_token"] is None
    assert body["requested_role"] == "judge"

    approval = db_session.scalar(
        select(RoleApproval).where(RoleApproval.user_id == body["user_id"])
    )
    assert approval is not None

    otp_req = client.post("/api/v1/auth/phone/request-otp", json={"phone": "89001234567"})
    assert otp_req.status_code == 200
    code = otp_req.json()["dev_otp"]
    assert code

    blocked = client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"phone": "89001234567", "code": code},
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "account_pending"

    approved = client.get(f"/api/v1/auth/approvals/{approval.token}/approve")
    assert approved.status_code == 200

    otp_req2 = client.post("/api/v1/auth/phone/request-otp", json={"phone": "89001234567"})
    code2 = otp_req2.json()["dev_otp"]
    login = client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"phone": "89001234567", "code": code2},
    )
    assert login.status_code == 200
    assert login.json()["role"] == "judge"


def test_phone_login_flow(client):
    reg = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79161234567",
            email="phone.user@example.com",
            display_name="Phone User",
        ),
    )
    assert reg.status_code == 200

    otp = client.post("/api/v1/auth/phone/request-otp", json={"phone": "9161234567"})
    assert otp.status_code == 200
    assert otp.json()["dev_otp"]

    login = client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"phone": "9161234567", "code": otp.json()["dev_otp"]},
    )
    assert login.status_code == 200
    assert login.json()["email"] == "phone.user@example.com"


def test_register_conflict_codes(client):
    payload = register_payload(
        phone="+79001112233",
        email="dup@example.com",
        display_name="Первый",
    )
    assert client.post("/api/v1/auth/register", json=payload).status_code == 200
    phone_taken = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "other@example.com"},
    )
    assert phone_taken.status_code == 409
    assert phone_taken.json()["error"]["code"] == "phone_taken"
    email_taken = client.post(
        "/api/v1/auth/register",
        json={**payload, "phone": "+79001112234"},
    )
    assert email_taken.status_code == 409
    assert email_taken.json()["error"]["code"] == "email_taken"


def test_patch_me_profile(client):
    reg = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79005554433",
            email="profile@example.com",
            display_name="Старое Имя",
        ),
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    patched = client.patch(
        "/api/v1/me",
        headers=headers,
        json={"display_name": "Новое Имя", "phone": "+79005554434"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["display_name"] == "Новое Имя"
    assert body["phone"]  # masked

    me = client.get("/api/v1/me", headers=headers)
    assert me.json()["display_name"] == "Новое Имя"

    conflict = client.patch(
        "/api/v1/me",
        headers=headers,
        json={"phone": "+79005554434"},
    )
    # same phone is fine
    assert conflict.status_code == 200

