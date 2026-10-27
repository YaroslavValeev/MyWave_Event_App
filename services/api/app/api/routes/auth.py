"""Auth routes: phone OTP, registration, role approval, dev login."""

from __future__ import annotations

from html import escape
from typing import Annotated

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.api.errors import raise_api_error
from app.domain.roles import EVENT_WRITE_ROLES, Role
from app.schemas.auth import (
    AthleteLinkListResponse,
    AthleteLinkOut,
    DevLoginRequest,
    LoginOptionsResponse,
    MeResponse,
    PendingApprovalItem,
    PendingApprovalListResponse,
    PhoneLoginRequest,
    PhoneOtpRequest,
    PhoneOtpResponse,
    PhoneOtpVerifyRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    RegisterResponse,
    RoleDecisionResponse,
    TokenResponse,
)
from app.services.athlete_id_service import canonical_athlete_id, ensure_athlete_id
from app.services.auth_service import (
    AuthError,
    decide_role_approval,
    decide_role_approval_by_id,
    dev_login,
    login_by_known_phone,
    list_pending_approvals,
    peek_role_approval,
    register_user,
    request_phone_otp,
    update_profile,
    verify_phone_otp,
)
from app.services.claim_service import ClaimError, confirm_link, list_links_for_user, reject_link
from app.services.phone_utils import mask_phone

router = APIRouter(tags=["auth"])


@router.get("/roles")
def list_roles() -> dict[str, object]:
    items = [role.value for role in Role]
    return {"items": items, "total": len(items)}


def _token_response(user, token: str) -> TokenResponse:
    return TokenResponse(
        access_token=token,
        role=Role(user.role),
        email=user.email,
        user_id=user.id,
        status=user.status,
        phone=mask_phone(user.phone),
        display_name=user.display_name,
        athlete_id=user.athlete_id,
    )


def _html_result(title: str, message: str) -> HTMLResponse:
    body = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>{escape(title)}</title></head>
<body style="font-family:system-ui;padding:2rem;max-width:40rem">
<h1>{escape(title)}</h1>
<p>{escape(message)}</p>
</body></html>"""
    return HTMLResponse(body)


def _html_confirm(token: str, decision: str, email: str, role: str) -> HTMLResponse:
    action = "утвердить" if decision == "approve" else "отклонить"
    title = "Подтверждение решения по роли"
    safe_token = escape(token, quote=True)
    body = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>{title}</title></head>
<body style="font-family:system-ui;padding:2rem;max-width:40rem">
<h1>{title}</h1>
<p>Заявка: {escape(email)}, роль «{escape(role)}».</p>
<p>Открытие письма статус не меняет. Нажмите кнопку, чтобы {escape(action)} заявку.</p>
<form method="post" action="/api/v1/auth/approvals/{safe_token}/confirm">
  <input type="hidden" name="decision" value="{escape(decision, quote=True)}">
  <button type="submit" style="font-size:1rem;padding:0.6rem 1rem">Подтвердить: {escape(action)}</button>
</form>
</body></html>"""
    return HTMLResponse(body)


def _require_staff(user) -> None:
    if Role(user.role) not in EVENT_WRITE_ROLES:
        raise_api_error(403, "forbidden", "Недостаточно прав для очереди ролей")


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
        athlete_id=user.athlete_id,
        access_token=token,
        token_type="bearer" if token else None,
    )


@router.get("/auth/login-options", response_model=LoginOptionsResponse)
def get_login_options(settings: AppSettings) -> LoginOptionsResponse:
    if settings.otp_challenge_required:
        return LoginOptionsResponse(
            otp_required=True,
            password_required=False,
            message="Код подтверждения придёт на email, привязанный к аккаунту. SMS пока не подключено.",
        )
    return LoginOptionsResponse(
        otp_required=False,
        password_required=False,
        message="Пока почтовая доставка не настроена, вход по номеру, который уже есть в системе. Роль берётся из аккаунта.",
    )


@router.post("/auth/phone/request-otp", response_model=PhoneOtpResponse)
def post_request_otp(
    body: PhoneOtpRequest, db: DbSession, settings: AppSettings
) -> PhoneOtpResponse:
    try:
        masked, ttl, dev_otp, email_masked = request_phone_otp(
            db, phone_raw=body.phone, settings=settings
        )
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)

    return PhoneOtpResponse(
        phone_masked=masked,
        email_masked=email_masked,
        message="Код подтверждения отправлен на email, привязанный к аккаунту. SMS пока не подключено.",
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


@router.post("/auth/phone/login", response_model=TokenResponse)
def post_phone_login(
    body: PhoneLoginRequest, db: DbSession, settings: AppSettings
) -> TokenResponse:
    try:
        user, token = login_by_known_phone(db, phone_raw=body.phone, settings=settings)
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _token_response(user, token)


@router.get("/auth/approvals/pending", response_model=PendingApprovalListResponse)
def get_pending_approvals(db: DbSession, user: CurrentUser) -> PendingApprovalListResponse:
    _require_staff(user)
    rows = list_pending_approvals(db)
    items: list[PendingApprovalItem] = []
    for approval, pending_user in rows:
        items.append(
            PendingApprovalItem(
                approval_id=approval.id,
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


@router.post("/auth/approvals/{approval_id}/approve", response_model=RoleDecisionResponse)
def post_approve_role(
    approval_id: int, db: DbSession, settings: AppSettings, user: CurrentUser
) -> RoleDecisionResponse:
    _require_staff(user)
    try:
        decided = decide_role_approval_by_id(
            db, approval_id=approval_id, approve=True, settings=settings
        )
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


@router.post("/auth/approvals/{approval_id}/reject", response_model=RoleDecisionResponse)
def post_reject_role(
    approval_id: int, db: DbSession, settings: AppSettings, user: CurrentUser
) -> RoleDecisionResponse:
    _require_staff(user)
    try:
        decided = decide_role_approval_by_id(
            db, approval_id=approval_id, approve=False, settings=settings
        )
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
def get_approve_role(token: str, db: DbSession) -> HTMLResponse:
    try:
        _approval, pending_user = peek_role_approval(db, token=token)
    except AuthError as exc:
        return _html_result("Ошибка", exc.message)
    return _html_confirm(
        token,
        "approve",
        pending_user.email,
        pending_user.requested_role or pending_user.role,
    )


@router.get("/auth/approvals/{token}/reject", response_class=HTMLResponse)
def get_reject_role(token: str, db: DbSession) -> HTMLResponse:
    try:
        _approval, pending_user = peek_role_approval(db, token=token)
    except AuthError as exc:
        return _html_result("Ошибка", exc.message)
    return _html_confirm(
        token,
        "reject",
        pending_user.email,
        pending_user.requested_role or pending_user.role,
    )


@router.post("/auth/approvals/{token}/confirm", response_class=HTMLResponse)
def post_email_confirm(
    token: str,
    db: DbSession,
    settings: AppSettings,
    decision: Annotated[str, Form()],
) -> HTMLResponse:
    if decision not in {"approve", "reject"}:
        return _html_result("Ошибка", "Некорректное решение")
    try:
        user = decide_role_approval(
            db, token=token, approve=decision == "approve", settings=settings
        )
    except AuthError as exc:
        return _html_result("Ошибка", exc.message)
    if decision == "approve":
        return _html_result(
            "Роль утверждена",
            f"Пользователь {user.email} активирован с ролью «{user.role}».",
        )
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


def _me_response(user, db=None) -> MeResponse:
    pending = 0
    athlete_id = user.athlete_id
    if db is not None:
        links = list_links_for_user(db, user=user)
        pending = sum(1 for item in links if item["status"] == "pending_claim")
        athlete_id = canonical_athlete_id(db, user)
    return MeResponse(
        id=user.id,
        email=user.email,
        phone=mask_phone(user.phone),
        role=Role(user.role),
        requested_role=Role(user.requested_role) if user.requested_role else None,
        status=user.status,
        display_name=user.display_name,
        athlete_id=athlete_id,
        pending_claim_count=pending,
    )


@router.get("/me", response_model=MeResponse)
def get_me(user: CurrentUser, db: DbSession) -> MeResponse:
    if not user.athlete_id:
        ensure_athlete_id(db, user)
        db.commit()
        db.refresh(user)
    return _me_response(user, db)


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
    return _me_response(updated, db)


@router.get("/me/athlete-links", response_model=AthleteLinkListResponse)
def get_athlete_links(user: CurrentUser, db: DbSession) -> AthleteLinkListResponse:
    items = [AthleteLinkOut.model_validate(row) for row in list_links_for_user(db, user=user)]
    return AthleteLinkListResponse(items=items, total=len(items))


@router.post("/me/athlete-links/{link_id}/confirm", response_model=AthleteLinkOut)
def post_confirm_athlete_link(
    link_id: int,
    user: CurrentUser,
    db: DbSession,
    settings: AppSettings,
) -> AthleteLinkOut:
    try:
        confirm_link(db, user=user, link_id=link_id, audit_enabled=settings.enable_audit_log)
    except ClaimError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    items = list_links_for_user(db, user=user)
    row = next((item for item in items if item["id"] == link_id), None)
    if row is None:
        raise_api_error(404, "not_found", "Связь не найдена")
    return AthleteLinkOut.model_validate(row)


@router.post("/me/athlete-links/{link_id}/reject", response_model=AthleteLinkOut)
def post_reject_athlete_link(
    link_id: int,
    user: CurrentUser,
    db: DbSession,
    settings: AppSettings,
) -> AthleteLinkOut:
    try:
        reject_link(db, user=user, link_id=link_id, audit_enabled=settings.enable_audit_log)
    except ClaimError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    items = list_links_for_user(db, user=user)
    row = next((item for item in items if item["id"] == link_id), None)
    if row is None:
        raise_api_error(404, "not_found", "Связь не найдена")
    return AthleteLinkOut.model_validate(row)
