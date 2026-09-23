"""Auth endpoint tests."""

from __future__ import annotations

import os

import pytest
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

    preview = client.get(f"/api/v1/auth/approvals/{approval.token}/approve")
    assert preview.status_code == 200
    assert "Подтвердить" in preview.text
    db_session.refresh(approval)
    assert approval.status == "pending"

    approved = client.post(
        f"/api/v1/auth/approvals/{approval.token}/confirm",
        data={"decision": "approve"},
    )
    assert approved.status_code == 200
    assert "утверждена" in approved.text.lower() or "Роль утверждена" in approved.text

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


def test_email_get_does_not_approve_without_confirm(client, db_session):
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79001230001",
            email="judge.prefetch@example.com",
            display_name="Судья Prefetch",
            requested_role="judge",
        ),
    )
    assert response.status_code == 200
    user_id = response.json()["user_id"]
    approval = db_session.scalar(select(RoleApproval).where(RoleApproval.user_id == user_id))
    assert approval is not None

    preview = client.get(f"/api/v1/auth/approvals/{approval.token}/approve")
    assert preview.status_code == 200
    assert "Подтвердить" in preview.text
    db_session.refresh(approval)
    assert approval.status == "pending"


def test_pending_list_hides_token(client, db_session):
    org = auth_header(client, "org.pending@example.com", "organizer")
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79001230002",
            email="judge.queue@example.com",
            display_name="Судья Очередь",
            requested_role="judge",
        ),
    )
    assert response.status_code == 200
    pending = client.get("/api/v1/auth/approvals/pending", headers=org)
    assert pending.status_code == 200
    items = pending.json()["items"]
    assert items
    assert "token" not in items[0]
    assert "approval_id" in items[0]


def test_otp_rate_limited(client):
    reg = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79001230003",
            email="otp.limit@example.com",
            display_name="OTP Limit",
        ),
    )
    assert reg.status_code == 200
    for _ in range(5):
        ok = client.post("/api/v1/auth/phone/request-otp", json={"phone": "+79001230003"})
        assert ok.status_code == 200
    blocked = client.post("/api/v1/auth/phone/request-otp", json={"phone": "+79001230003"})
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "otp_rate_limited"


def test_staff_approve_by_id(client, db_session):
    org = auth_header(client, "org.byid@example.com", "organizer")
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79001230004",
            email="judge.byid@example.com",
            display_name="Судья ById",
            requested_role="judge",
        ),
    )
    assert response.status_code == 200
    user_id = response.json()["user_id"]
    approval = db_session.scalar(select(RoleApproval).where(RoleApproval.user_id == user_id))
    assert approval is not None

    decided = client.post(
        f"/api/v1/auth/approvals/{approval.id}/approve",
        headers=org,
    )
    assert decided.status_code == 200, decided.text
    assert decided.json()["status"] == "active"
    assert decided.json()["role"] == "judge"


def test_login_options_without_smtp(client):
    response = client.get("/api/v1/auth/login-options")
    assert response.status_code == 200
    body = response.json()
    assert body["otp_required"] is False
    assert body["password_required"] is False


def test_phone_login_preserves_role_without_otp(client, db_session):
    org = auth_header(client, "org.phone.login@example.com", "organizer")
    registered = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79001230005",
            email="judge.phone.login@example.com",
            display_name="Судья Телефон",
            requested_role="judge",
        ),
    )
    assert registered.status_code == 200
    user_id = registered.json()["user_id"]
    approval = db_session.scalar(select(RoleApproval).where(RoleApproval.user_id == user_id))
    assert approval is not None
    decided = client.post(
        f"/api/v1/auth/approvals/{approval.id}/approve",
        headers=org,
    )
    assert decided.status_code == 200

    login = client.post("/api/v1/auth/phone/login", json={"phone": "+79001230005"})
    assert login.status_code == 200, login.text
    body = login.json()
    assert body["role"] == "judge"
    assert body["email"] == "judge.phone.login@example.com"

    again = client.post("/api/v1/auth/phone/login", json={"phone": "9001230005"})
    assert again.status_code == 200
    assert again.json()["role"] == "judge"
    assert again.json()["user_id"] == body["user_id"]


def test_phone_login_unknown_and_pending(client):
    missing = client.post("/api/v1/auth/phone/login", json={"phone": "+79000000000"})
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "user_not_found"

    pending = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            phone="+79001230006",
            email="judge.phone.pending@example.com",
            display_name="Судья Ожидает",
            requested_role="judge",
        ),
    )
    assert pending.status_code == 200
    blocked = client.post("/api/v1/auth/phone/login", json={"phone": "+79001230006"})
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "account_pending"


def test_phone_login_forbidden_when_smtp_configured(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.com")
    get_settings.cache_clear()
    try:
        options = client.get("/api/v1/auth/login-options")
        assert options.status_code == 200
        assert options.json()["otp_required"] is True
        forbidden = client.post(
            "/api/v1/auth/phone/login",
            json={"phone": "+79001112233"},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["error"]["code"] == "otp_required"
    finally:
        monkeypatch.setenv("SMTP_HOST", "")
        monkeypatch.setenv("SMTP_FROM", "")
        get_settings.cache_clear()


def test_phone_login_forbidden_in_production(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-not-for-production")
    get_settings.cache_clear()
    try:
        options = client.get("/api/v1/auth/login-options")
        assert options.status_code == 200
        assert options.json()["otp_required"] is True
        forbidden = client.post(
            "/api/v1/auth/phone/login",
            json={"phone": "+79001112233"},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["error"]["code"] == "otp_required"
    finally:
        monkeypatch.setenv("APP_ENV", "test")
        get_settings.cache_clear()


def test_production_rejects_insecure_secret(monkeypatch):
    from pydantic import ValidationError

    from app.config import Settings, get_settings

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "change-me-to-a-long-random-string")
    get_settings.cache_clear()
    try:
        with pytest.raises((ValidationError, ValueError)):
            Settings()
    finally:
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-not-for-production")
        get_settings.cache_clear()

