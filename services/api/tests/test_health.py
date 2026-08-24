"""Health and ready endpoint tests."""

from __future__ import annotations


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "app" in body
    assert "env" in body
    assert "time" in body
    assert "db_ok" in body
    assert body["db_ok"] is True
    assert body["status"] == "ok"


def test_ready_ok(client):
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["db_ok"] is True
