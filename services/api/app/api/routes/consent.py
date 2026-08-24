"""Legal catalog and user consents."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.api.errors import raise_api_error
from app.domain.consent import ALL_PURPOSES, CATALOG, CURRENT_VERSION, document_body, get_document
from app.schemas.consent import (
    ConsentGrantRequest,
    ConsentListResponse,
    ConsentOut,
    LegalDocumentListResponse,
    LegalDocumentOut,
)
from app.services.consent_service import ConsentError, grant_consent, list_user_consents, revoke_consent

router = APIRouter(tags=["consent"])


def _doc_out(purpose: str, *, include_body: bool, repo_root) -> LegalDocumentOut:
    doc = CATALOG[purpose]
    return LegalDocumentOut(
        purpose=doc.purpose,
        title=doc.title,
        version=doc.version,
        required=doc.required,
        revocable=doc.revocable,
        summary=doc.summary,
        body=document_body(repo_root, purpose) if include_body else None,
    )


@router.get("/legal/documents", response_model=LegalDocumentListResponse)
def list_legal_documents(settings: AppSettings) -> LegalDocumentListResponse:
    items = [_doc_out(purpose, include_body=False, repo_root=settings.repo_root) for purpose in ALL_PURPOSES]
    return LegalDocumentListResponse(items=items, current_version=CURRENT_VERSION)


@router.get("/legal/documents/{purpose}", response_model=LegalDocumentOut)
def get_legal_document(purpose: str, settings: AppSettings) -> LegalDocumentOut:
    if get_document(purpose) is None:
        raise_api_error(404, "unknown_purpose", "Документ не найден")
    return _doc_out(purpose, include_body=True, repo_root=settings.repo_root)


@router.get("/me/consents", response_model=ConsentListResponse)
def get_my_consents(db: DbSession, user: CurrentUser) -> ConsentListResponse:
    active = {row.purpose: row for row in list_user_consents(db, user_id=user.id)}
    items: list[ConsentOut] = []
    for purpose, doc in CATALOG.items():
        row = active.get(purpose)
        items.append(
            ConsentOut(
                purpose=purpose,
                title=doc.title,
                version=row.version if row else doc.version,
                required=doc.required,
                revocable=doc.revocable,
                granted=row is not None,
                granted_at=row.granted_at.isoformat() if row and row.granted_at else None,
                current_document_version=doc.version,
            )
        )
    return ConsentListResponse(items=items)


@router.post("/me/consents", response_model=ConsentOut)
def post_my_consent(
    body: ConsentGrantRequest,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ConsentOut:
    try:
        row = grant_consent(
            db,
            user=user,
            purpose=body.purpose,
            source="profile",
            settings=settings,
            version=body.version,
        )
        db.commit()
    except ConsentError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    doc = CATALOG[row.purpose]
    return ConsentOut(
        purpose=row.purpose,
        title=doc.title,
        version=row.version,
        required=doc.required,
        revocable=doc.revocable,
        granted=True,
        granted_at=row.granted_at.isoformat() if row.granted_at else None,
        current_document_version=doc.version,
    )


@router.post("/me/consents/{purpose}/revoke", response_model=ConsentOut)
def post_revoke_consent(
    purpose: str,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ConsentOut:
    try:
        row = revoke_consent(db, user=user, purpose=purpose, settings=settings)
        db.commit()
    except ConsentError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    doc = CATALOG[purpose]
    return ConsentOut(
        purpose=purpose,
        title=doc.title,
        version=row.version,
        required=doc.required,
        revocable=doc.revocable,
        granted=False,
        granted_at=None,
        current_document_version=doc.version,
    )
