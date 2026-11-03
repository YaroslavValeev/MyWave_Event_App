"""Official protocol revision snapshots — ADR-0017."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.api.errors import raise_api_error
from app.services.event_service import EventServiceError
from app.services.protocol_revision_service import (
    approve_revision,
    get_revision,
    list_revisions,
    revision_to_dict,
)

router = APIRouter(prefix="/events", tags=["protocol-revisions"])


class ApproveRevisionBody(BaseModel):
    note: str | None = Field(default=None, max_length=512)


@router.get("/{event_id}/official-protocol/revisions")
def get_revisions(event_id: int, db: DbSession, user: CurrentUser) -> dict:
    try:
        rows = list_revisions(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    items = [revision_to_dict(r) for r in rows]
    return {"items": items, "total": len(items)}


@router.post("/{event_id}/official-protocol/revisions", status_code=201)
def post_revision(
    event_id: int,
    body: ApproveRevisionBody,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> dict:
    try:
        row = approve_revision(
            db,
            event_id=event_id,
            actor=user,
            note=body.note,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return revision_to_dict(row)


@router.get("/{event_id}/official-protocol/revisions/{revision_id}")
def get_one_revision(
    event_id: int,
    revision_id: int,
    db: DbSession,
    user: CurrentUser,
) -> dict:
    try:
        row = get_revision(db, event_id=event_id, revision_id=revision_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    out = revision_to_dict(row)
    out["snapshot_json"] = row.snapshot_json
    return out


@router.get("/{event_id}/official-protocol/revisions/{revision_id}/download")
def download_revision(
    event_id: int,
    revision_id: int,
    db: DbSession,
    user: CurrentUser,
) -> Response:
    try:
        row = get_revision(db, event_id=event_id, revision_id=revision_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    filename = f"event-{event_id}-protocol-r{row.revision_no}.json"
    return Response(
        content=row.snapshot_json,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
