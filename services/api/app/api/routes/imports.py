"""Import Center routes — organizer only. No PII in responses except display names already on roster."""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.api.errors import raise_api_error
from app.schemas.importing import (
    ImportBatchListResponse,
    ImportBatchOut,
    ImportRowDecision,
    ImportRowOut,
    PackIngestOut,
    ScanProtocolOut,
)
from app.services.event_pack_service import files_from_uploads, ingest_pack
from app.services.protocol_pack_service import apply_scan_protocol
from app.services.event_service import EventServiceError
from app.services.import_service import (
    ImportServiceError,
    batch_public_dict,
    commit_batch,
    create_or_reuse_batch,
    decide_row,
    get_batch,
    list_batches,
    list_rows,
    row_public_dict,
)


router = APIRouter(prefix="/events", tags=["imports"])


def _raise(exc: ImportServiceError | EventServiceError) -> None:
    raise_api_error(exc.status_code, exc.code, exc.message)


@router.post("/{event_id}/imports", response_model=ImportBatchOut)
async def post_import_batch(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    file: UploadFile = File(...),
) -> ImportBatchOut:
    payload = await file.read()
    try:
        batch = create_or_reuse_batch(
            db,
            event_id=event_id,
            actor=user,
            filename=file.filename or "upload.xlsx",
            payload=payload,
            audit_enabled=settings.enable_audit_log,
        )
    except (ImportServiceError, EventServiceError) as exc:
        _raise(exc)
        raise
    rows = list_rows(db, batch_id=batch.id)
    return ImportBatchOut.model_validate(batch_public_dict(batch, rows))


@router.get("/{event_id}/imports", response_model=ImportBatchListResponse)
def get_import_batches(event_id: int, db: DbSession, user: CurrentUser) -> ImportBatchListResponse:
    try:
        batches = list_batches(db, event_id=event_id, actor=user)
    except (ImportServiceError, EventServiceError) as exc:
        _raise(exc)
        raise
    items = [ImportBatchOut.model_validate(batch_public_dict(b)) for b in batches]
    return ImportBatchListResponse(items=items, total=len(items))


@router.get("/{event_id}/imports/{batch_id}", response_model=ImportBatchOut)
def get_import_batch(event_id: int, batch_id: int, db: DbSession, user: CurrentUser) -> ImportBatchOut:
    try:
        batch = get_batch(db, event_id=event_id, batch_id=batch_id, actor=user)
    except (ImportServiceError, EventServiceError) as exc:
        _raise(exc)
        raise
    rows = list_rows(db, batch_id=batch.id)
    return ImportBatchOut.model_validate(batch_public_dict(batch, rows))


@router.patch("/{event_id}/imports/{batch_id}/rows/{row_id}", response_model=ImportRowOut)
def patch_import_row(
    event_id: int,
    batch_id: int,
    row_id: int,
    body: ImportRowDecision,
    db: DbSession,
    user: CurrentUser,
) -> ImportRowOut:
    try:
        row = decide_row(
            db,
            event_id=event_id,
            batch_id=batch_id,
            row_id=row_id,
            actor=user,
            decision=body.decision,
        )
    except (ImportServiceError, EventServiceError) as exc:
        _raise(exc)
        raise
    return ImportRowOut.model_validate(row_public_dict(row))


@router.post("/{event_id}/imports/{batch_id}/commit", response_model=ImportBatchOut)
def post_commit_import(
    event_id: int,
    batch_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ImportBatchOut:
    try:
        batch = commit_batch(
            db,
            event_id=event_id,
            batch_id=batch_id,
            actor=user,
            audit_enabled=settings.enable_audit_log,
        )
    except (ImportServiceError, EventServiceError) as exc:
        _raise(exc)
        raise
    rows = list_rows(db, batch_id=batch.id)
    return ImportBatchOut.model_validate(batch_public_dict(batch, rows))


@router.post("/{event_id}/ingest-pack", response_model=PackIngestOut)
async def post_ingest_pack(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    files: list[UploadFile] = File(...),
) -> PackIngestOut:
    payloads = await files_from_uploads(files)
    try:
        result = ingest_pack(
            db,
            event_id=event_id,
            actor=user,
            files=payloads,
            repo_root=settings.repo_root,
            audit_enabled=settings.enable_audit_log,
        )
    except (ImportServiceError, EventServiceError) as exc:
        _raise(exc)
        raise
    return PackIngestOut.model_validate(result)


@router.post("/{event_id}/scan-protocol", response_model=ScanProtocolOut)
def post_scan_protocol(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ScanProtocolOut:
    """Раскладывает транскрибированные сканы Казани в заезды, старты и черновики результатов."""
    try:
        result = apply_scan_protocol(
            db,
            event_id=event_id,
            actor=user,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        _raise(exc)
        raise
    return ScanProtocolOut.model_validate(result)
