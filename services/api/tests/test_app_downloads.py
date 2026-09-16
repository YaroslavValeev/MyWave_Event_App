"""App download catalog and analytics ingest tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.data.app_downloads_catalog import ARTIFACT_IDS
from app.services.app_downloads_service import (
    BUNDLED_DOCUMENTATION_PATH,
    DownloadConfigurationError,
    build_handoff,
    build_public_manifest,
    get_artifact_status,
    reset_handoff_limiter,
    validate_target,
)

TARGET_ENV_NAMES = (
    "MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL",
    "MYWAVE_EVENT_APP_IOS_TESTFLIGHT_URL",
    "MYWAVE_EVENT_APP_SOURCE_ARCHIVE_URL",
    "MYWAVE_EVENT_APP_DOCUMENTATION_URL",
)

ANALYTICS_EVENTS = (
    "mywave_event_app_card_viewed",
    "mywave_event_app_platform_selected",
    "mywave_event_app_download_clicked",
    "mywave_event_app_download_succeeded",
    "mywave_event_app_download_failed",
)


@pytest.fixture(autouse=True)
def clear_download_targets(monkeypatch):
    reset_handoff_limiter()
    for env_name in TARGET_ENV_NAMES:
        monkeypatch.delenv(env_name, raising=False)


def test_manifest_is_fail_closed_and_contains_all_formats():
    manifest = build_public_manifest()
    by_id = {item["id"]: item for item in manifest["artifacts"]}

    assert manifest["app"]["name"] == "MyWave Event App"
    assert tuple(item["id"] for item in manifest["artifacts"]) == ARTIFACT_IDS
    assert by_id["android"]["state"] == "unavailable"
    assert by_id["ios"]["state"] == "unavailable"
    assert by_id["source"]["state"] == "unavailable"
    assert by_id["documentation"]["state"] == "available"
    assert all("target_env" not in item for item in manifest["artifacts"])
    assert all("location" not in item for item in manifest["artifacts"])
    assert "Файлы доступны" in manifest["app"]["readiness"]


def test_placeholder_env_is_unavailable_not_error(monkeypatch):
    monkeypatch.setenv("MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL", "{{android_download_url}}")

    status = get_artifact_status("android")

    assert status["state"] == "unavailable"
    with pytest.raises(DownloadConfigurationError) as exc:
        build_handoff("android", api_public_url="http://127.0.0.1:8000")
    assert exc.value.unavailable is True


def test_real_https_target_becomes_available_without_leaking_url(monkeypatch):
    target = "https://downloads.example.org/releases/mywave-event-1.0.0.apk"
    monkeypatch.setenv("MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL", target)

    status = get_artifact_status("android")
    manifest_json = json.dumps(build_public_manifest(), ensure_ascii=False)

    assert status["state"] == "available"
    assert target not in manifest_json
    assert "location" not in status


@pytest.mark.parametrize(
    "target",
    (
        "http://downloads.example.org/app.apk",
        "https://localhost/app.apk",
        "https://127.0.0.1/app.apk",
        "file:///tmp/app.apk",
        "/etc/passwd",
        "/static/../instance/secret",
        "/downloads/../secret",
    ),
)
def test_unsafe_targets_are_rejected(monkeypatch, target):
    monkeypatch.setenv("MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL", target)

    assert get_artifact_status("android")["state"] == "error"
    with pytest.raises(DownloadConfigurationError) as exc:
        build_handoff("android", api_public_url="http://127.0.0.1:8000")
    assert exc.value.unavailable is False


def test_local_downloads_path_is_rewritten_to_api_origin(monkeypatch):
    monkeypatch.setenv("MYWAVE_EVENT_APP_DOCUMENTATION_URL", "/downloads/install-guide.pdf")

    handoff = build_handoff("documentation", api_public_url="http://127.0.0.1:8000")

    assert handoff["location"] == "http://127.0.0.1:8000/downloads/install-guide.pdf"
    assert handoff["open_in_new_tab"] is True


def test_validate_target_rejects_downloads_root():
    with pytest.raises(DownloadConfigurationError):
        validate_target("/downloads/")


def test_unknown_artifact_is_not_exposed():
    with pytest.raises(KeyError):
        get_artifact_status("unknown")
    with pytest.raises(KeyError):
        build_handoff("unknown", api_public_url="http://127.0.0.1:8000")


def test_manifest_api_does_not_expose_configured_target(client, monkeypatch):
    target = "https://downloads.example.org/mywave-event.apk"
    monkeypatch.setenv("MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL", target)

    response = client.get("/api/v1/app-downloads/manifest")
    payload = response.json()

    assert response.status_code == 200
    assert payload["artifacts"][0]["state"] == "available"
    assert target not in response.text
    assert response.headers["Cache-Control"].startswith("no-store")
    assert "{{android_download_url}}" not in response.text


def test_status_api_reports_unavailable_without_target(client):
    response = client.get("/api/v1/app-downloads/android/status")

    assert response.status_code == 200
    assert response.json()["state"] == "unavailable"


def test_handoff_api_rejects_missing_target(client):
    response = client.post("/api/v1/app-downloads/android/handoff", json={})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "artifact_unavailable"


def test_handoff_api_returns_validated_target(client, monkeypatch):
    target = "https://testflight.apple.com/join/example"
    monkeypatch.setenv("MYWAVE_EVENT_APP_IOS_TESTFLIGHT_URL", target)

    response = client.post("/api/v1/app-downloads/ios/handoff", json={})

    assert response.status_code == 200
    assert response.json()["location"] == target
    assert response.json()["open_in_new_tab"] is True


def test_handoff_unknown_artifact_is_404(client):
    response = client.post("/api/v1/app-downloads/windows/handoff", json={})
    assert response.status_code == 404


def test_analytics_accepts_download_events(client):
    response = client.post(
        "/api/v1/analytics/events",
        json={
            "event": "mywave_event_app_card_viewed",
            "context": "projects/checklist-org",
            "channel": "web",
            "meta": {"app_id": "mywave-event-app", "email": "secret@example.com"},
        },
    )
    assert response.status_code == 202
    assert response.json()["event"] == "mywave_event_app_card_viewed"


def test_analytics_rejects_unknown_event(client):
    response = client.post("/api/v1/analytics/events", json={"event": "not_a_real_event"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unknown_event"


def test_bundled_documentation_is_available_without_env():
    status = get_artifact_status("documentation")
    handoff = build_handoff("documentation", api_public_url="http://127.0.0.1:8000")

    assert status["state"] == "available"
    assert handoff["location"] == f"http://127.0.0.1:8000{BUNDLED_DOCUMENTATION_PATH}"
    assert BUNDLED_DOCUMENTATION_PATH not in json.dumps(build_public_manifest())


def test_bundled_documentation_file_is_served(client):
    response = client.get("/downloads/install-and-run.html")

    assert response.status_code == 200
    assert "MyWave Event App" in response.text
    assert "установка и запуск" in response.text.lower()


def test_handoff_rate_limit(client, monkeypatch):
    monkeypatch.setenv("MYWAVE_EVENT_APP_IOS_TESTFLIGHT_URL", "https://testflight.apple.com/join/example")
    monkeypatch.setattr("app.services.app_downloads_service.HANDOFF_RATE_LIMIT", 2)

    first = client.post("/api/v1/app-downloads/ios/handoff", json={})
    second = client.post("/api/v1/app-downloads/ios/handoff", json={})
    third = client.post("/api/v1/app-downloads/ios/handoff", json={})

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json()["error"]["code"] == "too_many_requests"


def test_frontend_defines_required_analytics_events():
    web_root = Path(__file__).resolve().parents[3] / "apps" / "web" / "src"
    sources = []
    for path in web_root.rglob("*.ts*"):
        sources.append(path.read_text(encoding="utf-8"))
    blob = "\n".join(sources)
    for event_name in ANALYTICS_EVENTS:
        assert event_name in blob, event_name
