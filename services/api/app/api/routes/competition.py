"""Competition nested routes under events."""

from __future__ import annotations

import json

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import select

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.api.errors import raise_api_error
from app.schemas.competition import (
    ApplicationCreate,
    ApplicationDecision,
    ApplicationListResponse,
    ApplicationOut,
    CategoryListResponse,
    CategoryOut,
    ChecklistItemOut,
    ChecklistListResponse,
    ChecklistUpdate,
    DocumentListResponse,
    DocumentOut,
    EventDetailOut,
    HeatCreate,
    HeatListResponse,
    HeatOut,
    HeatStatusUpdate,
    OfficialListResponse,
    OfficialOut,
    ParticipantListResponse,
    ParticipantOut,
    ResultDraftCreate,
    ResultHistoryListResponse,
    ResultHistoryOut,
    ResultListResponse,
    ResultOut,
    ResultStatusUpdate,
    RunListResponse,
    RunOut,
    ScheduleHint,
    StartListEntryCreate,
    StartListEntryOut,
    StartListFillRequest,
    StartListResponse,
    StartListStatusUpdate,
    TrainingSlotListResponse,
    TrainingSlotOut,
)
from app.schemas.protocol import ProtocolCaptureListResponse, ProtocolCaptureOut, ProtocolCaptureUpdate
from app.schemas.rules import EventRulesProfileOut, EventRulesProfileUpdate
from app.schemas.official_protocol import OfficialProtocolBundle
from app.schemas.scoring import (
    AggregateScoresOut,
    AggregateScoresRequest,
    JudgeScoreListResponse,
    JudgeScoreOut,
    JudgeScoreSubmit,
    ScoringEngineMetaOut,
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
from app.services.checklist_service import ensure_checklist, set_checklist_item
from app.services.competition_service import (
    event_counts,
    get_document,
    list_categories,
    list_documents,
    list_officials,
    list_participants,
    list_training_slots,
)
from app.services.document_service import delete_document, upload_document
from app.services.heat_service import (
    add_start_list_entry,
    create_heat,
    fill_start_list_from_roster,
    list_heats,
    list_runs_for_heat,
    list_start_list,
    update_heat_status,
    update_start_list_status,
)
from app.services.result_service import (
    list_result_history,
    list_results,
    transition_result,
    upsert_draft_result,
)
from app.services.protocol_service import (
    get_protocol_capture,
    list_protocol_captures,
    update_protocol_capture,
    upload_protocol_capture,
)
from app.services.rules_profile_service import get_rules_profile, profile_to_out, upsert_rules_profile
from app.services.official_protocol_service import (
    build_official_protocol_bundle,
    record_official_protocol_export,
    render_official_protocol_html,
)
from app.services.scoring_service import (
    aggregate_to_result,
    list_judge_scores,
    resolve_engine_for_event,
    score_out,
    submit_judge_score,
)
from app.domain.scoring_engines import engine_meta
from app.services.event_service import EventServiceError, get_event, is_event_archived
from app.models.protocol_capture import ProtocolCapture
from app.models.user import User as UserModel

router = APIRouter(prefix="/events", tags=["competition"])


def _protocol_out(capture: ProtocolCapture) -> ProtocolCaptureOut:
    extracted = None
    if capture.extracted_json:
        try:
            extracted = json.loads(capture.extracted_json)
        except json.JSONDecodeError:
            extracted = None
    return ProtocolCaptureOut(
        id=capture.id,
        event_id=capture.event_id,
        heat_id=capture.heat_id,
        title=capture.title,
        kind=capture.kind,
        status=capture.status,
        file_name=capture.file_name,
        mime_type=capture.mime_type,
        notes=capture.notes,
        extracted=extracted,
        created_by_user_id=capture.created_by_user_id,
        verified_by_user_id=capture.verified_by_user_id,
        verified_at=capture.verified_at,
        created_at=capture.created_at,
    )


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
        archived=is_event_archived(event),
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
    user_ids = {item.user_id for item in items if item.user_id}
    athlete_map: dict[int, str | None] = {}
    if user_ids:
        for row in db.scalars(select(UserModel).where(UserModel.id.in_(user_ids))).all():
            athlete_map[row.id] = row.athlete_id
    for item in items:
        out = ParticipantOut.model_validate(item)
        out.full_name = public_participant_name(db, item, user)
        if item.user_id:
            out.athlete_id = athlete_map.get(item.user_id)
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


@router.post("/{event_id}/documents", response_model=DocumentOut, status_code=201)
async def post_document(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    file: UploadFile = File(...),
    title: str = Form(...),
    kind: str = Form("other"),
    language: str | None = Form(None),
    description: str | None = Form(None),
) -> DocumentOut:
    try:
        doc = upload_document(
            db,
            event_id=event_id,
            actor=user,
            file=file,
            title=title,
            kind=kind,
            language=language,
            description=description,
            repo_root=settings.repo_root,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return DocumentOut.model_validate(doc)


@router.delete("/{event_id}/documents/{document_id}", status_code=204)
def remove_document(
    event_id: int,
    document_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> Response:
    try:
        delete_document(
            db,
            event_id=event_id,
            document_id=document_id,
            actor=user,
            repo_root=settings.repo_root,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return Response(status_code=204)


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


@router.get("/{event_id}/checklist", response_model=ChecklistListResponse)
def checklist(event_id: int, db: DbSession, user: CurrentUser) -> ChecklistListResponse:
    try:
        items = ensure_checklist(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    out = [ChecklistItemOut.model_validate(i) for i in items]
    return ChecklistListResponse(
        items=out,
        total=len(out),
        done_count=sum(1 for i in out if i.is_done),
    )


@router.patch("/{event_id}/checklist/{item_id}", response_model=ChecklistItemOut)
def patch_checklist(
    event_id: int,
    item_id: int,
    body: ChecklistUpdate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ChecklistItemOut:
    try:
        item = set_checklist_item(
            db,
            event_id=event_id,
            item_id=item_id,
            actor=user,
            is_done=body.is_done,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return ChecklistItemOut.model_validate(item)


@router.get("/{event_id}/heats", response_model=HeatListResponse)
def heats(event_id: int, db: DbSession, user: CurrentUser) -> HeatListResponse:
    try:
        items = list_heats(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return HeatListResponse(items=[HeatOut.model_validate(i) for i in items], total=len(items))


@router.post("/{event_id}/heats", response_model=HeatOut, status_code=201)
def post_heat(
    event_id: int,
    body: HeatCreate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> HeatOut:
    try:
        heat = create_heat(
            db,
            event_id=event_id,
            actor=user,
            code=body.code,
            title=body.title,
            heat_number=body.heat_number,
            category_id=body.category_id,
            scheduled_at=body.scheduled_at,
            notes=body.notes,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return HeatOut.model_validate(heat)


@router.patch("/{event_id}/heats/{heat_id}/status", response_model=HeatOut)
def patch_heat_status(
    event_id: int,
    heat_id: int,
    body: HeatStatusUpdate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> HeatOut:
    try:
        heat = update_heat_status(
            db,
            event_id=event_id,
            heat_id=heat_id,
            actor=user,
            status=body.status,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return HeatOut.model_validate(heat)


@router.get("/{event_id}/heats/{heat_id}/start-list", response_model=StartListResponse)
def start_list(
    event_id: int,
    heat_id: int,
    db: DbSession,
    user: CurrentUser,
) -> StartListResponse:
    try:
        items = list_start_list(db, event_id=event_id, heat_id=heat_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return StartListResponse(
        items=[StartListEntryOut.model_validate(i) for i in items],
        total=len(items),
    )


@router.post(
    "/{event_id}/heats/{heat_id}/start-list",
    response_model=StartListEntryOut,
    status_code=201,
)
def post_start_list_entry(
    event_id: int,
    heat_id: int,
    body: StartListEntryCreate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> StartListEntryOut:
    try:
        entry = add_start_list_entry(
            db,
            event_id=event_id,
            heat_id=heat_id,
            actor=user,
            participant_id=body.participant_id,
            start_order=body.start_order,
            bib_number=body.bib_number,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return StartListEntryOut.model_validate(entry)


@router.post(
    "/{event_id}/heats/{heat_id}/start-list/fill",
    response_model=StartListResponse,
    status_code=201,
)
def fill_start_list(
    event_id: int,
    heat_id: int,
    body: StartListFillRequest,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> StartListResponse:
    try:
        created = fill_start_list_from_roster(
            db,
            event_id=event_id,
            heat_id=heat_id,
            actor=user,
            category_id=body.category_id,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return StartListResponse(
        items=[StartListEntryOut.model_validate(i) for i in created],
        total=len(created),
    )


@router.patch(
    "/{event_id}/heats/{heat_id}/start-list/{entry_id}/status",
    response_model=StartListEntryOut,
)
def patch_start_list_status(
    event_id: int,
    heat_id: int,
    entry_id: int,
    body: StartListStatusUpdate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> StartListEntryOut:
    try:
        entry = update_start_list_status(
            db,
            event_id=event_id,
            heat_id=heat_id,
            entry_id=entry_id,
            actor=user,
            status=body.status,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return StartListEntryOut.model_validate(entry)


@router.get("/{event_id}/heats/{heat_id}/runs", response_model=RunListResponse)
def heat_runs(
    event_id: int,
    heat_id: int,
    db: DbSession,
    user: CurrentUser,
) -> RunListResponse:
    try:
        items = list_runs_for_heat(db, event_id=event_id, heat_id=heat_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return RunListResponse(items=[RunOut.model_validate(i) for i in items], total=len(items))


@router.get("/{event_id}/results", response_model=ResultListResponse)
def results(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    status: str | None = Query(default=None),
) -> ResultListResponse:
    try:
        items = list_results(db, event_id=event_id, actor=user, status=status)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return ResultListResponse(items=[ResultOut.model_validate(i) for i in items], total=len(items))


@router.post("/{event_id}/results", response_model=ResultOut, status_code=201)
def post_result(
    event_id: int,
    body: ResultDraftCreate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ResultOut:
    try:
        row = upsert_draft_result(
            db,
            event_id=event_id,
            actor=user,
            participant_id=body.participant_id,
            score=body.score,
            place=body.place,
            heat_id=body.heat_id,
            run_id=body.run_id,
            attempt_no=body.attempt_no,
            notes=body.notes,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return ResultOut.model_validate(row)


@router.patch("/{event_id}/results/{result_id}/status", response_model=ResultOut)
def patch_result_status(
    event_id: int,
    result_id: int,
    body: ResultStatusUpdate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ResultOut:
    try:
        row = transition_result(
            db,
            event_id=event_id,
            result_id=result_id,
            actor=user,
            status=body.status,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return ResultOut.model_validate(row)


@router.get("/{event_id}/results/{result_id}/history", response_model=ResultHistoryListResponse)
def result_history(
    event_id: int,
    result_id: int,
    db: DbSession,
    user: CurrentUser,
) -> ResultHistoryListResponse:
    try:
        items = list_result_history(db, event_id=event_id, result_id=result_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return ResultHistoryListResponse(
        items=[ResultHistoryOut.model_validate(i) for i in items],
        total=len(items),
    )


@router.get("/{event_id}/rules-profile", response_model=EventRulesProfileOut | None)
def event_rules_profile(event_id: int, db: DbSession, user: CurrentUser) -> EventRulesProfileOut | None:
    try:
        profile = get_rules_profile(db, event_id=event_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    if profile is None:
        return None
    return profile_to_out(profile)


@router.put("/{event_id}/rules-profile", response_model=EventRulesProfileOut)
def put_event_rules_profile(
    event_id: int,
    body: EventRulesProfileUpdate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> EventRulesProfileOut:
    try:
        profile = upsert_rules_profile(
            db,
            event_id=event_id,
            data=body,
            actor=user,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return profile_to_out(profile)


@router.get("/{event_id}/protocol-captures", response_model=ProtocolCaptureListResponse)
def protocol_captures(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    heat_id: int | None = Query(default=None),
) -> ProtocolCaptureListResponse:
    try:
        items = list_protocol_captures(db, event_id=event_id, actor=user, heat_id=heat_id)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    out = [_protocol_out(i) for i in items]
    return ProtocolCaptureListResponse(items=out, total=len(out))


@router.post("/{event_id}/protocol-captures", response_model=ProtocolCaptureOut, status_code=201)
async def post_protocol_capture(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    file: UploadFile = File(...),
    title: str = Form(...),
    kind: str = Form("judge_sheet"),
    heat_id: int | None = Form(None),
    notes: str | None = Form(None),
) -> ProtocolCaptureOut:
    try:
        capture = upload_protocol_capture(
            db,
            event_id=event_id,
            actor=user,
            file=file,
            title=title,
            kind=kind,
            heat_id=heat_id,
            notes=notes,
            repo_root=settings.repo_root,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _protocol_out(capture)


@router.patch("/{event_id}/protocol-captures/{capture_id}", response_model=ProtocolCaptureOut)
def patch_protocol_capture(
    event_id: int,
    capture_id: int,
    body: ProtocolCaptureUpdate,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> ProtocolCaptureOut:
    try:
        capture = update_protocol_capture(
            db,
            event_id=event_id,
            capture_id=capture_id,
            actor=user,
            data=body,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return _protocol_out(capture)


@router.get("/{event_id}/protocol-captures/{capture_id}/file")
def protocol_capture_file(
    event_id: int,
    capture_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> FileResponse:
    try:
        capture = get_protocol_capture(db, event_id=event_id, capture_id=capture_id, actor=user)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)

    base = settings.repo_root / "data" / "protocols"
    path = (base / capture.relative_path).resolve()
    if not str(path).startswith(str(base.resolve())):
        raise_api_error(400, "invalid_path", "Invalid protocol path")
    if not path.is_file():
        raise_api_error(404, "file_missing", "Protocol file is not available on server")
    return FileResponse(path, filename=capture.file_name, media_type=capture.mime_type)


@router.get("/{event_id}/scoring/engine", response_model=ScoringEngineMetaOut)
def scoring_engine_meta(event_id: int, db: DbSession, user: CurrentUser) -> ScoringEngineMetaOut:
    try:
        engine = resolve_engine_for_event(db, event_id=event_id, actor=user)
        meta = engine_meta(engine)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return ScoringEngineMetaOut.model_validate(meta)


@router.get("/{event_id}/judge-scores", response_model=JudgeScoreListResponse)
def judge_scores(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    participant_id: int | None = Query(default=None),
    heat_id: int | None = Query(default=None),
) -> JudgeScoreListResponse:
    try:
        items = list_judge_scores(
            db,
            event_id=event_id,
            actor=user,
            participant_id=participant_id,
            heat_id=heat_id,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    out = [JudgeScoreOut.model_validate(score_out(i)) for i in items]
    return JudgeScoreListResponse(items=out, total=len(out))


@router.post("/{event_id}/judge-scores", response_model=JudgeScoreOut, status_code=201)
def post_judge_score(
    event_id: int,
    body: JudgeScoreSubmit,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> JudgeScoreOut:
    try:
        row = submit_judge_score(
            db,
            event_id=event_id,
            actor=user,
            data=body,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return JudgeScoreOut.model_validate(score_out(row))


@router.post("/{event_id}/judge-scores/aggregate", response_model=AggregateScoresOut)
def post_aggregate_scores(
    event_id: int,
    body: AggregateScoresRequest,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> AggregateScoresOut:
    try:
        panel = aggregate_to_result(
            db,
            event_id=event_id,
            actor=user,
            participant_id=body.participant_id,
            heat_id=body.heat_id,
            attempt_no=body.attempt_no,
            write_result_draft=body.write_result_draft,
            place=body.place,
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return AggregateScoresOut(
        engine=panel["engine"],
        panel_score=panel["panel_score"],
        judge_count=panel["judge_count"],
        judge_totals=panel["judge_totals"],
        result_id=panel.get("result_id"),
        detail=panel.get("detail") or panel,
    )


@router.get("/{event_id}/official-protocol", response_model=OfficialProtocolBundle)
def official_protocol(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> OfficialProtocolBundle:
    try:
        bundle = build_official_protocol_bundle(db, event_id=event_id, actor=user)
        record_official_protocol_export(
            db,
            event_id=event_id,
            actor=user,
            export_format="json",
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    return bundle


@router.get("/{event_id}/official-protocol/download")
def official_protocol_download(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> Response:
    try:
        bundle = build_official_protocol_bundle(db, event_id=event_id, actor=user)
        record_official_protocol_export(
            db,
            event_id=event_id,
            actor=user,
            export_format="json_download",
            audit_enabled=settings.enable_audit_log,
        )
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)

    slug = bundle.event.get("slug") or f"event-{event_id}"
    payload = bundle.model_dump(mode="json")
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"{slug}-official-protocol.json"
    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{event_id}/official-protocol/html")
def official_protocol_html(
    event_id: int,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> Response:
    try:
        bundle = build_official_protocol_bundle(db, event_id=event_id, actor=user)
        record_official_protocol_export(
            db,
            event_id=event_id,
            actor=user,
            export_format="html",
            audit_enabled=settings.enable_audit_log,
        )
        page = render_official_protocol_html(bundle)
    except EventServiceError as exc:
        raise_api_error(exc.status_code, exc.code, exc.message)
    slug = bundle.event.get("slug") or f"event-{event_id}"
    return Response(
        content=page.encode("utf-8"),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'inline; filename="{slug}-official-protocol.html"'},
    )


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
