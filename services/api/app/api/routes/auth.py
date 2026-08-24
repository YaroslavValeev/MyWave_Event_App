"""Auth routes: phone OTP, registration, role approval, dev login."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.api.errors import raise_api_error
from app.domain.roles import Role
from app.schemas.auth import (
    DevLoginRequest,
    MeResponse,
    PendingApprovalItem,
    PendingApprovalListResponse,
    PhoneOtpRequest,
    PhoneOtpResponse,
    PhoneOtpVerifyRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    RegisterResponse,
    RoleDecisionResponse,
    TokenResponse,
)
from app.services.auth_service import (
    AuthError,
    decide_role_approval,
    dev_login,
    list_pending_approvals,
    register_user,
    request_phone_otp,
    update_profile,
    verify_phone_otp,
)
from app.services.phone_utils import mask_phone

router = APIRouter(tags=["auth"])


def _token_response(user, token: str) -> TokenResponse:
    return TokenResponse(
        access_token=token,
        role=Role(user.role),
        email=user.email,
        user_id=user.id,
        status=user.status,
        phone=mask_phone(user.phone),
        display_name=user.display_name,
    )


def _html_result(title: str, message: str) -> HTMLResponse:
    body = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>{title}</title></head>
<body style="font-family:system-ui;padding:2rem;max-width:40rem">
<h1>{title}</h1>
<p>{message}</p>
</body></html>"""
    return HTMLResponse(body)


@router.post("/auth/register", response_model=RegisterResponse)
def post_register(body: RegisterRequest, db: DbSession, settings: AppSettings) -> RegisterResponse:
    try:
        user, token = register_user(
            db,
            phone_raw=body.phone,
            email=str(body.email),
            display_name=body.display_name,
            requested_role=body.requested_role,
            settings=settings,
            accept_terms=body.accept_terms,
            accept_privacy=body.accept_privacy,
            accept_publish_name=body.accept_publish_name,
            accept_analytics=body.accept_analytics,
        )
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)

    if user.status == "active":
        message = "Регистрация завершена. Вы вошли как участник."
    else:
        message = (
            "Заявка принята. Роль будет активирована после утверждения "
            f"на {settings.owner_approval_email}."
        )

    return RegisterResponse(
        user_id=user.id,
        email=user.email,
        phone=mask_phone(user.phone) or "",
        role=Role(user.role),
        requested_role=Role(user.requested_role or user.role),
        status=user.status,
        message=message,
        access_token=token,
        token_type="bearer" if token else None,
    )


@router.post("/auth/phone/request-otp", response_model=PhoneOtpResponse)
def post_request_otp(
    body: PhoneOtpRequest, db: DbSession, settings: AppSettings
) -> PhoneOtpResponse:
    try:
        masked, ttl, dev_otp = request_phone_otp(db, phone_raw=body.phone, settings=settings)
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)

    return PhoneOtpResponse(
        phone_masked=masked,
        message="Код отправлен на email аккаунта (и в mail_outbox). SMS будет позже.",
        expires_in_seconds=ttl,
        dev_otp=dev_otp,
    )


@router.post("/auth/phone/verify-otp", response_model=TokenResponse)
def post_verify_otp(
    body: PhoneOtpVerifyRequest, db: DbSession, settings: AppSettings
) -> TokenResponse:
    try:
        user, token = verify_phone_otp(
            db, phone_raw=body.phone, code=body.code, settings=settings
        )
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _token_response(user, token)


@router.get("/auth/approvals/pending", response_model=PendingApprovalListResponse)
def get_pending_approvals(db: DbSession, user: CurrentUser) -> PendingApprovalListResponse:
    if Role(user.role) not in {
        Role.organizer,
        Role.event_admin,
        Role.platform_admin,
        Role.federation_manager,
    }:
        raise_api_error(403, "forbidden", "Недостаточно прав для очереди ролей")

    rows = list_pending_approvals(db)
    items: list[PendingApprovalItem] = []
    for approval, pending_user in rows:
        items.append(
            PendingApprovalItem(
                approval_id=approval.id,
                token=approval.token,
                user_id=pending_user.id,
                email=pending_user.email,
                display_name=pending_user.display_name,
                phone_masked=mask_phone(pending_user.phone),
                requested_role=Role(approval.requested_role),
                status=approval.status,
                created_at=approval.created_at.isoformat() if approval.created_at else "",
                expires_at=approval.expires_at.isoformat() if approval.expires_at else "",
            )
        )
    return PendingApprovalListResponse(items=items, total=len(items))


@router.post("/auth/approvals/{token}/approve", response_model=RoleDecisionResponse)
def post_approve_role(
    token: str, db: DbSession, settings: AppSettings, user: CurrentUser
) -> RoleDecisionResponse:
    if Role(user.role) not in {
        Role.organizer,
        Role.event_admin,
        Role.platform_admin,
        Role.federation_manager,
    }:
        raise_api_error(403, "forbidden", "Недостаточно прав")
    try:
        decided = decide_role_approval(db, token=token, approve=True, settings=settings)
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return RoleDecisionResponse(
        ok=True,
        user_id=decided.id,
        email=decided.email,
        role=Role(decided.role),
        status=decided.status,
        message="Роль утверждена",
    )


@router.post("/auth/approvals/{token}/reject", response_model=RoleDecisionResponse)
def post_reject_role(
    token: str, db: DbSession, settings: AppSettings, user: CurrentUser
) -> RoleDecisionResponse:
    if Role(user.role) not in {
        Role.organizer,
        Role.event_admin,
        Role.platform_admin,
        Role.federation_manager,
    }:
        raise_api_error(403, "forbidden", "Недостаточно прав")
    try:
        decided = decide_role_approval(db, token=token, approve=False, settings=settings)
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return RoleDecisionResponse(
        ok=True,
        user_id=decided.id,
        email=decided.email,
        role=Role(decided.role),
        status=decided.status,
        message="Роль отклонена",
    )


@router.get("/auth/approvals/{token}/approve", response_class=HTMLResponse)
def get_approve_role(token: str, db: DbSession, settings: AppSettings) -> HTMLResponse:
    try:
        user = decide_role_approval(db, token=token, approve=True, settings=settings)
    except AuthError as exc:
        return _html_result("Ошибка", exc.message)
    return _html_result(
        "Роль утверждена",
        f"Пользователь {user.email} активирован с ролью «{user.role}».",
    )


@router.get("/auth/approvals/{token}/reject", response_class=HTMLResponse)
def get_reject_role(token: str, db: DbSession, settings: AppSettings) -> HTMLResponse:
    try:
        user = decide_role_approval(db, token=token, approve=False, settings=settings)
    except AuthError as exc:
        return _html_result("Ошибка", exc.message)
    return _html_result(
        "Роль отклонена",
        f"Заявка пользователя {user.email} отклонена.",
    )


@router.post("/auth/dev-login", response_model=TokenResponse)
def post_dev_login(body: DevLoginRequest, db: DbSession, settings: AppSettings) -> TokenResponse:
    if settings.is_production or (
        not settings.is_development and settings.app_env != "test"
    ):
        raise_api_error(
            403,
            "dev_login_forbidden",
            "Dev login is only available when APP_ENV=development",
        )

    try:
        user, token = dev_login(db, email=str(body.email), role=body.role, settings=settings)
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)

    return _token_response(user, token)


def _me_response(user) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        phone=mask_phone(user.phone),
        role=Role(user.role),
        requested_role=Role(user.requested_role) if user.requested_role else None,
        status=user.status,
        display_name=user.display_name,
    )


@router.get("/me", response_model=MeResponse)
def get_me(user: CurrentUser) -> MeResponse:
    return _me_response(user)


@router.patch("/me", response_model=MeResponse)
def patch_me(
    body: ProfileUpdateRequest,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> MeResponse:
    if body.display_name is None and body.phone is None:
        raise_api_error(400, "empty_update", "Укажите display_name и/или phone")
    try:
        updated = update_profile(
            db,
            user=user,
            display_name=body.display_name,
            phone_raw=body.phone,
            settings=settings,
        )
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _me_response(updated)
