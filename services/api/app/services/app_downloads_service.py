"""Public manifest and safe handoff for MyWave Event App release artifacts."""

from __future__ import annotations

import ipaddress
import os
import shutil
from collections import defaultdict, deque
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from threading import Lock
from time import monotonic
from typing import Any
from urllib.parse import urlsplit

from app.data.app_downloads_catalog import APP_DOWNLOADS_CATALOG, ARTIFACT_IDS

HANDOFF_RATE_LIMIT = 20
HANDOFF_RATE_WINDOW_SECONDS = 60.0
LOCAL_DOWNLOAD_PREFIX = "/downloads/"
BUNDLED_DOCUMENTATION_PATH = "/downloads/install-and-run.html"
_BUNDLED_DOWNLOADS_DIR = Path(__file__).resolve().parents[1] / "static" / "downloads"

UNAVAILABLE_MESSAGE = "Файл временно недоступен: ссылка ещё не подключена."
AVAILABLE_MESSAGE = "Файл доступен для скачивания."
ERROR_MESSAGE = "Ошибка конфигурации файла. Повторите позже."
SUCCESS_MESSAGE = "Скачивание успешно запущено."


class DownloadConfigurationError(ValueError):
    """The release artifact configuration is incomplete or unsafe."""

    def __init__(self, message: str, *, unavailable: bool = False) -> None:
        super().__init__(message)
        self.unavailable = unavailable


class HandoffRateLimitError(RuntimeError):
    """Too many handoff attempts from one client."""


_handoff_hits: dict[str, deque[float]] = defaultdict(deque)
_handoff_lock = Lock()


def reset_handoff_limiter() -> None:
    with _handoff_lock:
        _handoff_hits.clear()


def check_handoff_rate(client_key: str) -> None:
    now = monotonic()
    with _handoff_lock:
        bucket = _handoff_hits[client_key]
        cutoff = now - HANDOFF_RATE_WINDOW_SECONDS
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= HANDOFF_RATE_LIMIT:
            raise HandoffRateLimitError("too_many_requests")
        bucket.append(now)


def _catalog() -> dict[str, Any]:
    return APP_DOWNLOADS_CATALOG


def _artifact_map(config: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    payload = config or _catalog()
    result: dict[str, dict[str, Any]] = {}
    for artifact in payload.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        artifact_id = str(artifact.get("id") or "").strip()
        if artifact_id in ARTIFACT_IDS and artifact_id not in result:
            result[artifact_id] = artifact
    return result


def sync_bundled_downloads(dest: Path) -> None:
    """Copy committed install artifacts into the writable downloads directory."""
    dest.mkdir(parents=True, exist_ok=True)
    if not _BUNDLED_DOWNLOADS_DIR.is_dir():
        return
    for src in _BUNDLED_DOWNLOADS_DIR.iterdir():
        if src.is_file():
            shutil.copy2(src, dest / src.name)


def _target_for(artifact: dict[str, Any]) -> str:
    env_name = str(artifact.get("target_env") or "").strip()
    value = (os.getenv(env_name) or "").strip() if env_name else ""
    if str(artifact.get("id") or "") == "documentation" and _is_unconfigured(value):
        return BUNDLED_DOCUMENTATION_PATH
    return value


def _is_unconfigured(value: str) -> bool:
    stripped = (value or "").strip()
    if not stripped:
        return True
    return "{{" in stripped or "}}" in stripped


def validate_target(target: str) -> str:
    """Allow HTTPS or controlled /downloads/ paths; reject SSRF-like targets."""
    value = (target or "").strip()
    if _is_unconfigured(value):
        raise DownloadConfigurationError("Файл ещё не подключён", unavailable=True)

    if value.startswith("/"):
        parsed_path = PurePosixPath(value.split("?", 1)[0].split("#", 1)[0])
        if ".." in parsed_path.parts or not value.startswith(LOCAL_DOWNLOAD_PREFIX):
            raise DownloadConfigurationError("Недопустимый локальный путь")
        if parsed_path == PurePosixPath("/downloads") or value.rstrip("/") == "/downloads":
            raise DownloadConfigurationError("Недопустимый локальный путь")
        return value

    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise DownloadConfigurationError("Разрешены только публичные HTTPS-ссылки")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise DownloadConfigurationError("Локальный адрес запрещён")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise DownloadConfigurationError("Непубличный IP-адрес запрещён")
    return value


def _public_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    target = _target_for(artifact)
    state = "unavailable"
    message = UNAVAILABLE_MESSAGE
    if target and not _is_unconfigured(target):
        try:
            validate_target(target)
            state = "available"
            message = AVAILABLE_MESSAGE
        except DownloadConfigurationError:
            state = "error"
            message = ERROR_MESSAGE

    return {
        "id": str(artifact.get("id") or ""),
        "label": str(artifact.get("label") or ""),
        "platform": str(artifact.get("platform") or ""),
        "format": str(artifact.get("format") or ""),
        "version": str(artifact.get("version") or "Не опубликована"),
        "size": artifact.get("size") or None,
        "last_updated": str(artifact.get("last_updated") or "Не указана"),
        "action_label": str(artifact.get("action_label") or "Скачать"),
        "requirements": [
            str(item) for item in artifact.get("requirements", []) if str(item).strip()
        ],
        "state": state,
        "message": message,
    }


def build_unavailable_manifest() -> dict[str, Any]:
    artifacts = []
    for artifact in _artifact_map().values():
        public = _public_artifact(artifact)
        public["state"] = "error"
        public["message"] = "Каталог временно недоступен."
        artifacts.append(public)
    app = deepcopy(_catalog()["app"])
    app["readiness"] = "Каталог временно недоступен"
    app["available_count"] = 0
    return {
        "app": app,
        "artifacts": artifacts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_public_manifest() -> dict[str, Any]:
    """Return UI-safe metadata without release target URLs or environment names."""
    config = _catalog()
    app = deepcopy(config["app"])
    artifacts = [_public_artifact(item) for item in _artifact_map(config).values()]
    available_count = sum(item["state"] == "available" for item in artifacts)
    app["readiness"] = (
        "Файлы доступны"
        if available_count
        else "Веб-приложение готово. Нативные файлы ожидают подключения"
    )
    app["available_count"] = available_count
    return {
        "app": app,
        "artifacts": artifacts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_artifact_status(artifact_id: str) -> dict[str, Any]:
    artifact = _artifact_map().get(artifact_id)
    if artifact is None:
        raise KeyError(artifact_id)
    return _public_artifact(artifact)


def resolve_handoff_location(target: str, *, api_public_url: str) -> str:
    if target.startswith("/"):
        return f"{api_public_url.rstrip('/')}{target}"
    return target


def build_handoff(artifact_id: str, *, api_public_url: str) -> dict[str, Any]:
    """Resolve a validated target only after an explicit user confirmation."""
    artifact = _artifact_map().get(artifact_id)
    if artifact is None:
        raise KeyError(artifact_id)
    target = validate_target(_target_for(artifact))
    return {
        "artifact_id": artifact_id,
        "location": resolve_handoff_location(target, api_public_url=api_public_url),
        "open_in_new_tab": bool(artifact.get("open_in_new_tab")),
        "message": SUCCESS_MESSAGE,
    }
