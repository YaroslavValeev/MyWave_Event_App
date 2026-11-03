"""Publication feed API — ADR-0013."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Header, Query, Response, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import AppSettings, CurrentUser, DbSession, OptionalUser
from app.api.errors import raise_api_error
from app.schemas.publication import (
    PublicationCreate,
    PublicationListResponse,
    PublicationModerate,
    PublicationOut,
    PublicationUpdate,
)
from app.services.event_service import EventServiceError
from app.services.publication_service import (
    add_publication_media,
    create_publication,
    delete_publication,
    get_publication,
    list_publications,
    moderate_publication,
    publication_to_dict,
    publishable_author_roles_for,
    resolve_media_path,
    update_publication,
)

router = APIRouter(prefix="/events/{event_id}/publications", tags=["publications"])


def _out(pub) -> PublicationOut:
    return PublicationOut.model_validate(publication_to_dict(pub))


@router.get("/author-roles")
def get_author_roles(event_id: int, db: DbSession, user: CurrentUser) -> dict:
    """Roles available for 'publish as' — currently only the actor's own role."""
    from app.services.event_service import get_event

    try:
        get_event(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return {"roles": publishable_author_roles_for(user)}


@router.get("", response_model=PublicationListResponse)
def get_publications(
    event_id: int,
    db: DbSession,
    user: OptionalUser,
    status: Annotated[str | None, Query()] = None,
) -> PublicationListResponse:
    try:
        items = list_publications(db, event_id=event_id, actor=user, status=status)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    out = [_out(i) for i in items]
    return PublicationListResponse(items=out, total=len(out))


@router.post("", response_model=PublicationOut, status_code=201)
def post_publication(
    event_id: int,
    body: PublicationCreate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PublicationOut:
    if idempotency_key and not body.idempotency_key:
        body = body.model_copy(update={"idempotency_key": idempotency_key})
    try:
        pub = create_publication(
            db,
            event_id=event_id,
            actor=user,
            data=body,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _out(pub)


@router.get("/{publication_id}", response_model=PublicationOut)
def get_one_publication(
    event_id: int,
    publication_id: int,
    db: DbSession,
    user: OptionalUser,
) -> PublicationOut:
    try:
        pub = get_publication(
            db, event_id=event_id, publication_id=publication_id, actor=user
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _out(pub)


@router.patch("/{publication_id}", response_model=PublicationOut)
def patch_publication(
    event_id: int,
    publication_id: int,
    body: PublicationUpdate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> PublicationOut:
    try:
        pub = update_publication(
            db,
            event_id=event_id,
            publication_id=publication_id,
            actor=user,
            data=body,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _out(pub)


@router.post("/{publication_id}/moderate", response_model=PublicationOut)
def post_moderate(
    event_id: int,
    publication_id: int,
    body: PublicationModerate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> PublicationOut:
    try:
        pub = moderate_publication(
            db,
            event_id=event_id,
            publication_id=publication_id,
            actor=user,
            data=body,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _out(pub)


@router.delete("/{publication_id}", status_code=204, response_class=Response)
def remove_publication(
    event_id: int,
    publication_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> Response:
    try:
        delete_publication(
            db,
            event_id=event_id,
            publication_id=publication_id,
            actor=user,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return Response(status_code=204)


@router.post("/{publication_id}/media", response_model=PublicationOut, status_code=201)
async def post_media(
    event_id: int,
    publication_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    file: UploadFile = File(...),
) -> PublicationOut:
    try:
        pub = add_publication_media(
            db,
            event_id=event_id,
            publication_id=publication_id,
            actor=user,
            file=file,
            data_dir=settings.data_dir,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _out(pub)


@router.get("/{publication_id}/media/{media_id}/file")
def download_media(
    event_id: int,
    publication_id: int,
    media_id: int,
    db: DbSession,
    user: OptionalUser,
    settings: AppSettings,
) -> FileResponse:
    try:
        media, path = resolve_media_path(
            db,
            event_id=event_id,
            publication_id=publication_id,
            media_id=media_id,
            actor=user,
            data_dir=settings.data_dir,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return FileResponse(path, filename=media.file_name, media_type=media.mime_type)
