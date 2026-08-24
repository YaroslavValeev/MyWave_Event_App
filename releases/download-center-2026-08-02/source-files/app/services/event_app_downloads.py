"""Public manifest and safe handoff for MyWave Event app release artifacts."""

from __future__ import annotations

import ipaddress
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

import yaml

ARTIFACT_IDS = ("android", "ios", "source", "documentation")
ARTIFACT_FALLBACKS = (
    ("android", "Android", "Android", "APK / AAB"),
    ("ios", "iOS / TestFlight", "iOS", "TestFlight"),
    ("source", "Исходный код", "Разработка", "ZIP"),
    ("documentation", "Документация", "Все платформы", "PDF / HTML / ZIP"),
)
DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "configs" / "event_app_downloads.yaml"
)


class DownloadConfigurationError(ValueError):
    """The release artifact configuration is incomplete or unsafe."""


def build_unavailable_manifest() -> dict[str, Any]:
    """Keep the page usable when the YAML catalog itself cannot be read."""
    artifacts = []
    for artifact_id, label, platform, file_format in ARTIFACT_FALLBACKS:
        artifacts.append(
            {
                "id": artifact_id,
                "label": label,
                "platform": platform,
                "format": file_format,
                "version": "Не опубликована",
                "size": None,
                "last_updated": "Не указана",
                "action_label": "Скачать",
                "requirements": [],
                "state": "error",
                "message": "Каталог временно недоступен.",
            }
        )
    return {
        "app": {
            "id": "mywave-event-app",
            "name": "MyWave Event app",
            "short_description": "Мобильный помощник участника и организатора MyWave.",
            "features": [],
            "version": "Не опубликована",
            "last_updated": "Не указана",
            "platforms": [item[1] for item in ARTIFACT_FALLBACKS],
            "readiness": "Каталог временно недоступен",
            "available_count": 0,
        },
        "artifacts": artifacts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise DownloadConfigurationError("Не удалось прочитать конфигурацию") from exc

    if not isinstance(payload.get("app"), dict) or not isinstance(
        payload.get("artifacts"), list
    ):
        raise DownloadConfigurationError("Некорректная структура конфигурации")
    return payload


def _artifact_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for artifact in config.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        artifact_id = str(artifact.get("id") or "").strip()
        if artifact_id in ARTIFACT_IDS and artifact_id not in result:
            result[artifact_id] = artifact
    return result


def _target_for(artifact: dict[str, Any]) -> str:
    env_name = str(artifact.get("target_env") or "").strip()
    if not env_name:
        return ""
    return (os.getenv(env_name) or "").strip()


def _validate_target(target: str) -> str:
    """Allow HTTPS or explicit site-local release paths; reject SSRF-like targets."""
    value = (target or "").strip()
    if not value or "{{" in value or "}}" in value:
        raise DownloadConfigurationError("Файл ещё не подключён")

    if value.startswith("/"):
        parsed_path = PurePosixPath(value.split("?", 1)[0].split("#", 1)[0])
        if ".." in parsed_path.parts or not value.startswith(
            ("/static/", "/downloads/")
        ):
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
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(
        ".local"
    ):
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
    message = "Файл временно недоступен: ссылка ещё не подключена."
    if target:
        try:
            _validate_target(target)
            state = "available"
            message = "Файл доступен для скачивания."
        except DownloadConfigurationError:
            state = "error"
            message = "Ошибка конфигурации файла. Повторите позже."

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


def build_public_manifest(config_path: str | Path | None = None) -> dict[str, Any]:
    """Return UI-safe metadata without release target URLs or environment names."""
    config = _load_config(config_path)
    app = deepcopy(config["app"])
    artifacts = [_public_artifact(item) for item in _artifact_map(config).values()]
    available_count = sum(item["state"] == "available" for item in artifacts)
    app["readiness"] = (
        "Файлы доступны"
        if available_count
        else "Интеграция готова — файлы ожидают подключения"
    )
    app["available_count"] = available_count
    return {
        "app": app,
        "artifacts": artifacts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_artifact_status(
    artifact_id: str, config_path: str | Path | None = None
) -> dict[str, Any]:
    config = _load_config(config_path)
    artifact = _artifact_map(config).get(artifact_id)
    if artifact is None:
        raise KeyError(artifact_id)
    return _public_artifact(artifact)


def build_handoff(
    artifact_id: str, config_path: str | Path | None = None
) -> dict[str, Any]:
    """Resolve a validated target only after an explicit user confirmation."""
    config = _load_config(config_path)
    artifact = _artifact_map(config).get(artifact_id)
    if artifact is None:
        raise KeyError(artifact_id)
    target = _validate_target(_target_for(artifact))
    return {
        "artifact_id": artifact_id,
        "location": target,
        "open_in_new_tab": bool(artifact.get("open_in_new_tab")),
        "message": "Скачивание успешно запущено.",
    }
