"""Contract tests for the MyWave Event app Download Center."""

from __future__ import annotations

import json

import pytest

from app.services.event_app_downloads import (
    ARTIFACT_IDS,
    DownloadConfigurationError,
    build_handoff,
    build_public_manifest,
    build_unavailable_manifest,
    get_artifact_status,
)

TARGET_ENV_NAMES = (
    "MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL",
    "MYWAVE_EVENT_APP_IOS_TESTFLIGHT_URL",
    "MYWAVE_EVENT_APP_SOURCE_ARCHIVE_URL",
    "MYWAVE_EVENT_APP_DOCUMENTATION_URL",
)


@pytest.fixture(autouse=True)
def clear_download_targets(monkeypatch):
    for env_name in TARGET_ENV_NAMES:
        monkeypatch.delenv(env_name, raising=False)


def test_manifest_is_fail_closed_and_contains_all_formats():
    manifest = build_public_manifest()

    assert manifest["app"]["name"] == "MyWave Event app"
    assert tuple(item["id"] for item in manifest["artifacts"]) == ARTIFACT_IDS
    assert all(item["state"] == "unavailable" for item in manifest["artifacts"])
    assert all("target_env" not in item for item in manifest["artifacts"])
    assert "Интеграция готова" in manifest["app"]["readiness"]


def test_fallback_manifest_keeps_all_download_options_visible():
    manifest = build_unavailable_manifest()

    assert tuple(item["id"] for item in manifest["artifacts"]) == ARTIFACT_IDS
    assert all(item["state"] == "error" for item in manifest["artifacts"])


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
        "{{android_download_url}}",
    ),
)
def test_unsafe_or_placeholder_targets_are_rejected(monkeypatch, target):
    monkeypatch.setenv("MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL", target)

    assert get_artifact_status("android")["state"] == "error"
    with pytest.raises(DownloadConfigurationError):
        build_handoff("android")


def test_handoff_returns_target_only_after_explicit_request(monkeypatch):
    target = "/static/css/branding.css"
    monkeypatch.setenv("MYWAVE_EVENT_APP_DOCUMENTATION_URL", target)

    handoff = build_handoff("documentation")

    assert handoff["location"] == target
    assert handoff["artifact_id"] == "documentation"
    assert handoff["open_in_new_tab"] is True


def test_unknown_artifact_is_not_exposed():
    with pytest.raises(KeyError):
        get_artifact_status("unknown")
    with pytest.raises(KeyError):
        build_handoff("unknown")


def test_checklist_page_contains_accessible_download_center(client):
    response = client.get("/projects/checklist-org")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="mywave-event-app"' in html
    assert 'role="tablist"' in html
    assert 'aria-live="polite"' in html
    assert "MyWave Event app" in html
    assert "{{android_download_url}}" not in html


def test_manifest_api_does_not_expose_configured_target(client, monkeypatch):
    target = "https://downloads.example.org/mywave-event.apk"
    monkeypatch.setenv("MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL", target)

    response = client.get("/api/event-app-downloads/manifest")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["artifacts"][0]["state"] == "available"
    assert target not in response.get_data(as_text=True)
    assert response.headers["Cache-Control"].startswith("no-store")


def test_status_api_reports_unavailable_without_target(client):
    response = client.get("/api/event-app-downloads/android/status")

    assert response.status_code == 200
    assert response.get_json()["state"] == "unavailable"


def test_handoff_api_rejects_missing_target(client):
    response = client.post("/api/event-app-downloads/android/handoff", json={})

    assert response.status_code == 503
    assert response.get_json()["error"] == "artifact_unavailable"


def test_handoff_api_returns_validated_target(client, monkeypatch):
    target = "https://testflight.apple.com/join/example"
    monkeypatch.setenv("MYWAVE_EVENT_APP_IOS_TESTFLIGHT_URL", target)

    response = client.post("/api/event-app-downloads/ios/handoff", json={})

    assert response.status_code == 200
    assert response.get_json()["location"] == target


def test_frontend_defines_required_analytics_events():
    source = open("static/js/event_app_downloads.js", encoding="utf-8").read()

    for event_name in (
        "mywave_event_app_card_viewed",
        "mywave_event_app_platform_selected",
        "mywave_event_app_download_clicked",
        "mywave_event_app_download_succeeded",
        "mywave_event_app_download_failed",
    ):
        assert event_name in source
