"""Audit routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from app.api.deps import DbSession, require_audit_reader
from app.models.user import User
from app.services.audit_service import list_audit_events

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    actor_user_id: int | None
    actor_email: str | None
    entity_type: str | None
    entity_id: str | None
    payload_json: str | None
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditEventRead]
    total: int


@router.get("", response_model=AuditListResponse)
def get_audit(
    db: DbSession,
    _: Annotated[User, Depends(require_audit_reader)],
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> AuditListResponse:
    items = list_audit_events(db, limit=limit, offset=offset)
    return AuditListResponse(
        items=[AuditEventRead.model_validate(item) for item in items],
        total=len(items),
    )
