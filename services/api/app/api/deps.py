"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.errors import raise_api_error
from app.config import Settings, get_settings
from app.db import get_db
from app.domain.roles import AUDIT_READ_ROLES, Role
from app.models.user import User
from app.services.auth_service import AuthError, decode_access_token, get_user_by_id

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: DbSession,
    settings: AppSettings,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> User:
    if credentials is None or not credentials.credentials:
        raise_api_error(401, "unauthorized", "Authentication required")

    try:
        payload = decode_access_token(credentials.credentials, settings)
    except AuthError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise_api_error(401, "invalid_token", "Invalid access token subject")

    user = get_user_by_id(db, user_id)
    if user is None:
        raise_api_error(401, "user_not_found", "User for token no longer exists")
    if user.status == "rejected":
        raise_api_error(403, "account_rejected", "Account was rejected")
    if user.status == "pending":
        raise_api_error(403, "account_pending", "Account is pending role approval")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_audit_reader(user: CurrentUser) -> User:
    if Role(user.role) not in AUDIT_READ_ROLES:
        raise_api_error(403, "forbidden", "Audit access requires event_admin or platform_admin")
    return user
