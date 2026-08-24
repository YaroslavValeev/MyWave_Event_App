"""Competition nested routes under events."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.api.errors import raise_api_error
from app.schemas.competition import (
    ApplicationCreate,
    ApplicationDecision,
    ApplicationListResponse,
    ApplicationOut,
    CategoryListResponse,
    CategoryOut,
    DocumentListResponse,
    DocumentOut,
    EventDetailOut,
    OfficialListResponse,
    OfficialOut,
    ParticipantListResponse,
    ParticipantOut,
    ScheduleHint,
    TrainingSlotListResponse,
    TrainingSlotOut,
)
from app.schemas.event import EventRead
from app.services.consent_service import public_participant_name
from app.services.application_service import (
    ApplicationError,
    create_application,
    decide_application,
    get_my_application,
    list_applications,
)
from app.services.competition_service import (
    event_counts,
    get_document,
    list_categories,
    list_documents,
    list_officials,
    list_participants,
    list_training_slots,
)
from app.services.event_service import EventServiceError, get_event

router = APIRouter(prefix="/events", tags=["competition"])


@router.get("/{event_id}/detail", response_model=EventDetailOut)
def event_detail(event_id: int, db: DbSession, user: CurrentUser) -> EventDetailOut:
    try:
        event = get_event(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    cats, parts, docs, offs, slots = event_counts(db, event)
    base = EventRead.model_validate(event)
    return EventDetailOut(
        **base.model_dump(),
        categories_count=cats,
        participants_count=parts,
        documents_count=docs,
        officials_count=offs,
        training_slots_count=slots,
    )


@router.get("/{event_id}/categories", response_model=CategoryListResponse)
def categories(event_id: int, db: DbSession, user: CurrentUser) -> CategoryListResponse:
    try:
        items = list_categories(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return CategoryListResponse(items=[CategoryOut.model_validate(i) for i in items], total=len(items))


@router.get("/{event_id}/participants", response_model=ParticipantListResponse)
def participants(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    category_id: int | None = Query(default=None),
) -> ParticipantListResponse:
    try:
        items = list_participants(db, event_id=event_id, actor=user, category_id=category_id)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    masked: list[ParticipantOut] = []
    for item in items:
        out = ParticipantOut.model_validate(item)
        out.full_name = public_participant_name(db, item, user)
        masked.append(out)
    return ParticipantListResponse(items=masked, total=len(masked))


@router.post("/{event_id}/applications", response_model=ApplicationOut, status_code=201)
def post_application(
    event_id: int,
    body: ApplicationCreate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ApplicationOut:
    try:
        part = create_application(
            db,
            event_id=event_id,
            actor=user,
            category_id=body.category_id,
            club=body.club,
            region=body.region,
            city=body.city,
            gender=body.gender,
            birth_year=body.birth_year,
            audit_enabled=settings.enable_audit_log,
        )
    except (ApplicationError, EventServiceError) as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return ApplicationOut.model_validate(part)


@router.get("/{event_id}/applications/me", response_model=ApplicationOut | None)
def my_application(event_id: int, db: DbSession, user: CurrentUser) -> ApplicationOut | None:
    try:
        part = get_my_application(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    if part is None:
        return None
    return ApplicationOut.model_validate(part)


@router.get("/{event_id}/applications", response_model=ApplicationListResponse)
def applications(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    status: str | None = Query(default="pending"),
) -> ApplicationListResponse:
    try:
        items = list_applications(db, event_id=event_id, actor=user, status=status)
    except (ApplicationError, EventServiceError) as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return ApplicationListResponse(
        items=[ApplicationOut.model_validate(i) for i in items],
        total=len(items),
    )


@router.patch("/{event_id}/applications/{participant_id}", response_model=ApplicationOut)
def patch_application(
    event_id: int,
    participant_id: int,
    body: ApplicationDecision,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ApplicationOut:
    try:
        part = decide_application(
            db,
            event_id=event_id,
            participant_id=participant_id,
            actor=user,
            status=body.status,
            audit_enabled=settings.enable_audit_log,
        )
    except (ApplicationError, EventServiceError) as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return ApplicationOut.model_validate(part)


@router.get("/{event_id}/officials", response_model=OfficialListResponse)
def officials(event_id: int, db: DbSession, user: CurrentUser) -> OfficialListResponse:
    try:
        items = list_officials(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return OfficialListResponse(items=[OfficialOut.model_validate(i) for i in items], total=len(items))


@router.get("/{event_id}/training-slots", response_model=TrainingSlotListResponse)
def training_slots(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    discipline: str | None = Query(default=None),
    only_booked: bool = Query(default=False),
) -> TrainingSlotListResponse:
    try:
        items = list_training_slots(
            db,
            event_id=event_id,
            actor=user,
            discipline=discipline,
            only_booked=only_booked,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return TrainingSlotListResponse(
        items=[TrainingSlotOut.model_validate(i) for i in items],
        total=len(items),
    )


@router.get("/{event_id}/documents", response_model=DocumentListResponse)
def documents(event_id: int, db: DbSession, user: CurrentUser) -> DocumentListResponse:
    try:
        items = list_documents(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return DocumentListResponse(items=[DocumentOut.model_validate(i) for i in items], total=len(items))


@router.get("/{event_id}/documents/{document_id}/file")
def document_file(
    event_id: int,
    document_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> FileResponse:
    try:
        doc = get_document(db, event_id=event_id, document_id=document_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)

    base = settings.repo_root / "data" / "documents"
    path = (base / doc.relative_path).resolve()
    if not str(path).startswith(str(base.resolve())):
        raise_api_error(400, "invalid_path", "Invalid document path")
    if not path.is_file():
        raise_api_error(404, "file_missing", "Document file is not available on server")
    suffix = path.suffix.lower()
    media = {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
    }.get(suffix, "application/octet-stream")
    return FileResponse(path, filename=doc.file_name, media_type=media)


@router.get("/{event_id}/schedule-hint", response_model=ScheduleHint)
def schedule_hint(event_id: int, db: DbSession, user: CurrentUser) -> ScheduleHint:
    try:
        event = get_event(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    _ = event
    return ScheduleHint(
        summary=(
            "Официальные тренировки 11–12.08.2026: Вейкборд — оз. Кабан; "
            "Вейксерф — ул. Торфяная, 83. Актуальные слоты загружены из Excel."
        ),
        notes=[
            "11.08 — запасной тренировочный день",
            "12.08 — основные тренировочные слоты",
            "13.08 — квалификация · 14.08 полуфиналы · 15.08 финалы · 16.08 резерв",
            "Вкладка «ЧП России» в Excel — реестр заявок (не расписание); телефоны импортируются в User для phone-login",
        ],
    )
