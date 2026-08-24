"""Auth service: JWT, phone OTP, registration, role approval."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.domain.roles import Role
from app.models.auth_extra import PhoneOtp, RoleApproval
from app.models.user import User
from app.services.audit_service import append_audit
from app.services.consent_service import ConsentError, grant_registration_consents
from app.services.mail_service import send_email
from app.services.phone_utils import mask_phone, normalize_phone

AUTO_APPROVE_ROLES: frozenset[Role] = frozenset({Role.participant})
MAX_OTP_ATTEMPTS = 5


class AuthError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 401) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def create_access_token(*, user: User, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "typ": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str, settings: Settings) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("token_expired", "Access token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("invalid_token", "Invalid access token") from exc
    if payload.get("typ") != "access":
        raise AuthError("invalid_token", "Invalid access token type")
    return payload


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_user_by_phone(db: Session, phone: str) -> User | None:
    return db.scalar(select(User).where(User.phone == phone))


def get_or_create_user(db: Session, *, email: str, role: Role) -> User:
    user = get_user_by_email(db, email)
    if user is None:
        user = User(
            email=email.lower(),
            role=role.value,
            status="active",
            display_name=email.split("@")[0],
        )
        db.add(user)
        db.flush()
    else:
        user.role = role.value
        user.status = "active"
        db.add(user)
        db.flush()
    return user


def _hash_otp(code: str, settings: Settings) -> str:
    material = f"{settings.secret_key}:otp:{code}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _require_normalized_phone(raw: str) -> str:
    phone = normalize_phone(raw)
    if not phone:
        raise AuthError("invalid_phone", "Некорректный номер телефона", status_code=400)
    return phone


def register_user(
    db: Session,
    *,
    phone_raw: str,
    email: str,
    display_name: str,
    requested_role: Role,
    settings: Settings,
    accept_terms: bool = False,
    accept_privacy: bool = False,
    accept_publish_name: bool = False,
    accept_analytics: bool = False,
) -> tuple[User, str | None]:
    phone = _require_normalized_phone(phone_raw)
    email_l = email.lower().strip()

    if get_user_by_phone(db, phone):
        raise AuthError("phone_taken", "Этот телефон уже зарегистрирован", status_code=409)
    if get_user_by_email(db, email_l):
        raise AuthError("email_taken", "Этот email уже зарегистрирован", status_code=409)

    auto = requested_role in AUTO_APPROVE_ROLES
    user = User(
        email=email_l,
        phone=phone,
        display_name=display_name.strip(),
        requested_role=requested_role.value,
        role=requested_role.value if auto else Role.participant.value,
        status="active" if auto else "pending",
    )
    db.add(user)
    db.flush()

    token: str | None = None
    if auto:
        token = create_access_token(user=user, settings=settings)
        append_audit(
            db,
            action="auth.register.auto_approved",
            actor_user_id=user.id,
            actor_email=user.email,
            entity_type="user",
            entity_id=str(user.id),
            payload={"role": user.role, "phone_masked": mask_phone(phone)},
            enabled=settings.enable_audit_log,
        )
    else:
        _create_role_approval(db, user=user, settings=settings)
        append_audit(
            db,
            action="auth.register.pending_approval",
            actor_user_id=user.id,
            actor_email=user.email,
            entity_type="user",
            entity_id=str(user.id),
            payload={
                "requested_role": requested_role.value,
                "phone_masked": mask_phone(phone),
            },
            enabled=settings.enable_audit_log,
        )

    try:
        grant_registration_consents(
            db,
            user=user,
            accept_terms=accept_terms,
            accept_privacy=accept_privacy,
            accept_publish_name=accept_publish_name,
            accept_analytics=accept_analytics,
            settings=settings,
        )
    except ConsentError as exc:
        raise AuthError(exc.code, exc.message, status_code=exc.status_code) from exc

    db.commit()
    db.refresh(user)
    return user, token


def update_profile(
    db: Session,
    *,
    user: User,
    display_name: str | None,
    phone_raw: str | None,
    settings: Settings,
) -> User:
    if display_name is not None:
        user.display_name = display_name

    if phone_raw is not None:
        phone = _require_normalized_phone(phone_raw)
        owner = get_user_by_phone(db, phone)
        if owner is not None and owner.id != user.id:
            raise AuthError("phone_taken", "Этот телефон уже зарегистрирован", status_code=409)
        user.phone = phone

    db.add(user)
    append_audit(
        db,
        action="auth.profile.update",
        actor_user_id=user.id,
        actor_email=user.email,
        entity_type="user",
        entity_id=str(user.id),
        payload={
            "display_name": user.display_name,
            "phone_masked": mask_phone(user.phone),
        },
        enabled=settings.enable_audit_log,
    )
    db.commit()
    db.refresh(user)
    return user


def request_phone_otp(
    db: Session,
    *,
    phone_raw: str,
    settings: Settings,
) -> tuple[str, int, str | None]:
    phone = _require_normalized_phone(phone_raw)
    user = get_user_by_phone(db, phone)
    if user is None:
        raise AuthError(
            "user_not_found",
            "Пользователь с этим телефоном не найден. Сначала зарегистрируйтесь.",
            status_code=404,
        )
    if user.status == "rejected":
        raise AuthError(
            "account_rejected",
            "Аккаунт отклонён. Обратитесь к организатору.",
            status_code=403,
        )

    code = _generate_otp()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_ttl_minutes)
    db.add(
        PhoneOtp(
            phone=phone,
            code_hash=_hash_otp(code, settings),
            expires_at=expires,
            attempts=0,
        )
    )
    db.flush()

    body = (
        f"Здравствуйте{', ' + user.display_name if user.display_name else ''}!\n\n"
        f"Код входа в MyWave Event App: {code}\n"
        f"Действует {settings.otp_ttl_minutes} мин.\n\n"
        f"Телефон: {mask_phone(phone)}\n"
        "Если вы не запрашивали код — проигнорируйте письмо.\n"
        "\n"
        "Примечание: SMS-доставка будет подключена позже; сейчас код уходит на email аккаунта.\n"
    )
    send_email(
        settings=settings,
        to_email=user.email,
        subject="Код входа MyWave Event App",
        body=body,
    )
    # Also mirror to owner outbox path for ops visibility in local/dev without PII spam to owner inbox.
    append_audit(
        db,
        action="auth.otp_requested",
        actor_user_id=user.id,
        actor_email=user.email,
        entity_type="user",
        entity_id=str(user.id),
        payload={"phone_masked": mask_phone(phone)},
        enabled=settings.enable_audit_log,
    )
    db.commit()

    dev_otp = code if (settings.is_development or settings.app_env == "test") else None
    return mask_phone(phone) or phone, settings.otp_ttl_minutes * 60, dev_otp


def verify_phone_otp(
    db: Session,
    *,
    phone_raw: str,
    code: str,
    settings: Settings,
) -> tuple[User, str]:
    phone = _require_normalized_phone(phone_raw)
    user = get_user_by_phone(db, phone)
    if user is None:
        raise AuthError("user_not_found", "Пользователь не найден", status_code=404)
    if user.status == "rejected":
        raise AuthError("account_rejected", "Аккаунт отклонён", status_code=403)
    if user.status == "pending":
        raise AuthError(
            "account_pending",
            "Аккаунт ожидает утверждения роли организатором.",
            status_code=403,
        )

    otp = db.scalar(
        select(PhoneOtp)
        .where(PhoneOtp.phone == phone)
        .order_by(PhoneOtp.id.desc())
        .limit(1)
    )
    if otp is None:
        raise AuthError("otp_missing", "Сначала запросите код", status_code=400)

    now = datetime.now(timezone.utc)
    expires = otp.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        raise AuthError("otp_expired", "Код истёк. Запросите новый.", status_code=400)
    if otp.attempts >= MAX_OTP_ATTEMPTS:
        raise AuthError("otp_locked", "Слишком много попыток. Запросите новый код.", status_code=429)

    otp.attempts += 1
    db.add(otp)
    if otp.code_hash != _hash_otp(code.strip(), settings):
        db.commit()
        raise AuthError("otp_invalid", "Неверный код", status_code=400)

    # Invalidate used OTP
    otp.expires_at = now
    db.add(otp)

    token = create_access_token(user=user, settings=settings)
    append_audit(
        db,
        action="auth.phone_login",
        actor_user_id=user.id,
        actor_email=user.email,
        entity_type="user",
        entity_id=str(user.id),
        payload={"phone_masked": mask_phone(phone), "role": user.role},
        enabled=settings.enable_audit_log,
    )
    db.commit()
    db.refresh(user)
    return user, token


def _create_role_approval(db: Session, *, user: User, settings: Settings) -> RoleApproval:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    approval = RoleApproval(
        user_id=user.id,
        token=token,
        requested_role=user.requested_role or Role.participant.value,
        status="pending",
        expires_at=expires,
    )
    db.add(approval)
    db.flush()

    approve_url = f"{settings.api_public_url.rstrip('/')}/api/v1/auth/approvals/{token}/approve"
    reject_url = f"{settings.api_public_url.rstrip('/')}/api/v1/auth/approvals/{token}/reject"
    body = (
        "Новая заявка на роль в MyWave Event App\n\n"
        f"Имя: {user.display_name}\n"
        f"Email: {user.email}\n"
        f"Телефон: {mask_phone(user.phone)}\n"
        f"Запрошенная роль: {approval.requested_role}\n\n"
        f"Утвердить:\n{approve_url}\n\n"
        f"Отклонить:\n{reject_url}\n\n"
        "Ссылки действуют 7 дней.\n"
    )
    send_email(
        settings=settings,
        to_email=settings.owner_approval_email,
        subject=f"[MyWave] Заявка на роль: {approval.requested_role}",
        body=body,
    )
    return approval


def list_pending_approvals(db: Session) -> list[tuple[RoleApproval, User]]:
    rows = db.execute(
        select(RoleApproval, User)
        .join(User, User.id == RoleApproval.user_id)
        .where(RoleApproval.status == "pending")
        .order_by(RoleApproval.id.desc())
    ).all()
    return [(approval, user) for approval, user in rows]


def decide_role_approval(
    db: Session,
    *,
    token: str,
    approve: bool,
    settings: Settings,
) -> User:
    approval = db.scalar(select(RoleApproval).where(RoleApproval.token == token))
    if approval is None:
        raise AuthError("approval_not_found", "Заявка не найдена", status_code=404)
    if approval.status != "pending":
        raise AuthError("approval_decided", "Заявка уже обработана", status_code=409)

    now = datetime.now(timezone.utc)
    expires = approval.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        approval.status = "expired"
        db.add(approval)
        db.commit()
        raise AuthError("approval_expired", "Срок заявки истёк", status_code=410)

    user = get_user_by_id(db, approval.user_id)
    if user is None:
        raise AuthError("user_not_found", "Пользователь не найден", status_code=404)

    if approve:
        approval.status = "approved"
        approval.decided_at = now
        user.role = approval.requested_role
        user.status = "active"
        action = "auth.role_approved"
        message_subject = "Роль утверждена — MyWave Event App"
        message_body = (
            f"Ваша роль «{user.role}» утверждена. Можно войти по номеру телефона.\n"
        )
    else:
        approval.status = "rejected"
        approval.decided_at = now
        user.status = "rejected"
        action = "auth.role_rejected"
        message_subject = "Роль отклонена — MyWave Event App"
        message_body = (
            "Заявка на роль отклонена. Напишите организатору, если нужна другая роль.\n"
        )

    db.add(approval)
    db.add(user)
    append_audit(
        db,
        action=action,
        actor_user_id=None,
        actor_email=settings.owner_approval_email,
        entity_type="user",
        entity_id=str(user.id),
        payload={"requested_role": approval.requested_role, "status": user.status},
        enabled=settings.enable_audit_log,
    )
    send_email(
        settings=settings,
        to_email=user.email,
        subject=message_subject,
        body=message_body,
    )
    db.commit()
    db.refresh(user)
    return user


def dev_login(
    db: Session,
    *,
    email: str,
    role: Role,
    settings: Settings,
) -> tuple[User, str]:
    if not settings.is_development and settings.app_env != "test":
        raise AuthError(
            "dev_login_forbidden",
            "Dev login is only available when APP_ENV=development",
            status_code=403,
        )
    user = get_or_create_user(db, email=email, role=role)
    token = create_access_token(user=user, settings=settings)
    append_audit(
        db,
        action="auth.dev_login",
        actor_user_id=user.id,
        actor_email=user.email,
        entity_type="user",
        entity_id=str(user.id),
        payload={"role": user.role},
        enabled=settings.enable_audit_log,
    )
    db.commit()
    db.refresh(user)
    return user, token
