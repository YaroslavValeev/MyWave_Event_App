"""Product analytics ingest (Stage 1 sink: audit table + stdout)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Response, status

from app.api.deps import DbSession
from app.api.errors import raise_api_error
from app.config import get_settings
from app.schemas.app_downloads import AnalyticsEventAccepted, AnalyticsEventIn
from app.services.audit_service import append_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

ALLOWED_EVENTS = frozenset(
    {
        "mwe_app_opened",
        "mwe_auth_login_succeeded",
        "mwe_auth_login_failed",
        "mwe_event_viewed",
        "mwe_event_created",
        "mwe_event_published",
        "mwe_entry_submitted",
        "mwe_notification_opened",
        "mwe_consent_granted",
        "mwe_consent_revoked",
        "mwe_legal_document_viewed",
        "mwe_result_draft_saved",
        "mwe_roster_locked",
        "mwe_result_published",
        "mwe_permission_denied",
        "mywave_event_app_card_viewed",
        "mywave_event_app_platform_selected",
        "mywave_event_app_download_clicked",
        "mywave_event_app_download_succeeded",
        "mywave_event_app_download_failed",
    }
)

_SAFE_PROPERTY_KEYS = frozenset(
    {
        "app_id",
        "app_version",
        "artifact_id",
        "channel",
        "event_id",
        "reason",
        "reason_code",
        "stage",
        "version",
        "route_or_action",
        "unread_count",
        "purpose",
        "count",
        "entity_type",
        "result_id",
        "entry_id",
    }
)


def _sanitize_properties(raw: dict[str, Any] | None) -> dict[str, Any]:
    if not raw:
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in _SAFE_PROPERTY_KEYS:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            if isinstance(value, str) and len(value) > 80:
                cleaned[key] = value[:80]
            else:
                cleaned[key] = value
    return cleaned


@router.post("/events", response_model=AnalyticsEventAccepted, status_code=status.HTTP_202_ACCEPTED)
def ingest_analytics_event(
    body: AnalyticsEventIn,
    response: Response,
    db: DbSession,
) -> AnalyticsEventAccepted:
    response.headers["Cache-Control"] = "no-store"
    event_name = body.event.strip()
    if event_name not in ALLOWED_EVENTS:
        raise_api_error(status.HTTP_400_BAD_REQUEST, "unknown_event", "Неизвестное событие аналитики")

    properties = _sanitize_properties(body.properties or body.meta)
    payload = {
        "event": event_name,
        "context": body.context,
        "channel": body.channel or "web",
        "properties": properties,
    }
    logger.info("analytics event=%s context=%s", event_name, body.context)
    append_audit(
        db,
        action=f"analytics.{event_name}",
        entity_type="analytics",
        entity_id=str(properties.get("artifact_id") or properties.get("event_id") or ""),
        payload=payload,
        enabled=get_settings().enable_audit_log,
    )
    db.commit()
    return AnalyticsEventAccepted(event=event_name)
