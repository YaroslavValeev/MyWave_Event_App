from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.domain.roles import AUDIT_READ_ROLES, WRITE_EVENT_ROLES, EventStatus, Role
from app.models import AuditEvent, Event, User
from app.schemas import EventCreate, EventUpdate

ALGORITHM = "HS256"
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(*, user_id: str, role: str, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def write_audit(
    db: Session,
    *,
    action: str,
    actor_id: str | None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    payload: dict[str, Any] | None = None,
    enabled: bool = True,
) -> None:
    if not enabled:
        return
    db.add(
        AuditEvent(
            action=action,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            payload_json=json.dumps(payload or {}, ensure_ascii=False),
        )
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Требуется токен доступа"},
        )
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("missing sub")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Недействительный токен"},
        ) from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "user_not_found", "message": "Пользователь не найден"},
        )
    return user


def require_roles(*roles: Role):
    allowed = set(roles)

    def _checker(user: User = Depends(get_current_user)) -> User:
        if Role(user.role) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "forbidden", "message": "Недостаточно прав"},
            )
        return user

    return _checker


def check_db(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def upsert_dev_user(db: Session, *, email: str, role: Role, display_name: str | None) -> User:
    user = db.scalar(select(User).where(User.email == email))
    name = display_name or email.split("@")[0]
    if user is None:
        user = User(email=email, display_name=name, role=role.value)
        db.add(user)
    else:
        user.role = role.value
        user.display_name = name
    db.flush()
    return user


def list_events_for_user(db: Session, user: User | None) -> list[Event]:
    stmt = select(Event).order_by(Event.created_at.desc())
    events = list(db.scalars(stmt))
    if user is None:
        return [e for e in events if e.status != EventStatus.DRAFT.value]
    role = Role(user.role)
    if role in WRITE_EVENT_ROLES or role == Role.PLATFORM_ADMIN:
        return events
    return [e for e in events if e.status != EventStatus.DRAFT.value]


def create_event(db: Session, payload: EventCreate, user: User, settings: Settings) -> Event:
    if Role(user.role) not in WRITE_EVENT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Недостаточно прав для создания события"},
        )
    existing = db.scalar(select(Event).where(Event.slug == payload.slug))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "slug_conflict", "message": "Событие с таким slug уже существует"},
        )
    event = Event(
        slug=payload.slug,
        title=payload.title,
        description=payload.description,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        status=payload.status.value,
        created_by=user.id,
    )
    db.add(event)
    db.flush()
    write_audit(
        db,
        action="event.created",
        actor_id=user.id,
        resource_type="event",
        resource_id=event.id,
        payload={"slug": event.slug, "status": event.status},
        enabled=settings.enable_audit_log,
    )
    return event


def update_event(
    db: Session, event_id: str, payload: EventUpdate, user: User, settings: Settings
) -> Event:
    if Role(user.role) not in WRITE_EVENT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Недостаточно прав для изменения события"},
        )
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Событие не найдено"},
        )
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        data["status"] = data["status"].value if hasattr(data["status"], "value") else data["status"]
    for key, value in data.items():
        setattr(event, key, value)
    db.flush()
    write_audit(
        db,
        action="event.updated",
        actor_id=user.id,
        resource_type="event",
        resource_id=event.id,
        payload=data,
        enabled=settings.enable_audit_log,
    )
    return event


def list_audit(db: Session, user: User) -> list[AuditEvent]:
    if Role(user.role) not in AUDIT_READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Недостаточно прав для audit"},
        )
    return list(db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200)))
