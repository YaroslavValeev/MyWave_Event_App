"""App download catalog: public manifest, status, validated handoff."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.errors import error_payload, raise_api_error
from app.config import get_settings
from app.schemas.app_downloads import AppDownloadArtifactOut, AppDownloadHandoffOut, AppDownloadManifestOut
from app.services.app_downloads_service import (
    DownloadConfigurationError,
    HandoffRateLimitError,
    build_handoff,
    build_public_manifest,
    check_handoff_rate,
    get_artifact_status,
)

router = APIRouter(prefix="/app-downloads", tags=["app-downloads"])

_NO_STORE_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
}


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _apply_no_store(response: Response) -> None:
    for key, value in _NO_STORE_HEADERS.items():
        response.headers[key] = value


@router.get("/manifest", response_model=AppDownloadManifestOut)
def download_manifest(response: Response) -> AppDownloadManifestOut:
    _apply_no_store(response)
    payload = build_public_manifest()
    return AppDownloadManifestOut.model_validate(payload)


@router.get("/{artifact_id}/status", response_model=AppDownloadArtifactOut)
def download_status(artifact_id: str, response: Response) -> AppDownloadArtifactOut:
    _apply_no_store(response)
    try:
        payload = get_artifact_status(artifact_id)
    except KeyError:
        raise_api_error(status.HTTP_404_NOT_FOUND, "not_found", "Вариант скачивания не найден")
    return AppDownloadArtifactOut.model_validate(payload)


@router.post("/{artifact_id}/handoff", response_model=AppDownloadHandoffOut)
def download_handoff(artifact_id: str, request: Request, response: Response) -> AppDownloadHandoffOut | JSONResponse:
    _apply_no_store(response)
    try:
        check_handoff_rate(_client_key(request))
        payload = build_handoff(artifact_id, api_public_url=get_settings().api_public_url)
    except KeyError:
        raise_api_error(status.HTTP_404_NOT_FOUND, "not_found", "Вариант скачивания не найден")
    except HandoffRateLimitError:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_payload(
                "too_many_requests",
                "Слишком много попыток скачивания. Подождите минуту и повторите.",
            ),
            headers=_NO_STORE_HEADERS,
        )
    except DownloadConfigurationError as exc:
        code = "artifact_unavailable" if exc.unavailable else "artifact_misconfigured"
        message = (
            "Файл временно недоступен. Ссылка ещё не подключена."
            if exc.unavailable
            else "Не удалось начать скачивание: ошибка конфигурации файла."
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_payload(code, message),
            headers=_NO_STORE_HEADERS,
        )
    return AppDownloadHandoffOut.model_validate(payload)
