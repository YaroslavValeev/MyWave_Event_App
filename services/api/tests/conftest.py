"""Pytest fixtures for API Stage 1."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure test env before app import
os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ENABLE_AUDIT_LOG"] = "1"
os.environ["CORS_ORIGINS"] = "http://testclient"
# Phone login without OTP is allowed only when SMTP is off; isolate tests from local .env.
os.environ["SMTP_HOST"] = ""
os.environ["SMTP_FROM"] = ""

from app.config import get_settings
from app.db import get_db
from app.main import create_app
from app.models import Base


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    get_settings.cache_clear()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    import app.db as db_module

    app = create_app()

    def _override_get_db() -> Generator[Session, None, None]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        # Lifespan init_db may create a separate in-memory engine — rebind to ours.
        db_module._engine = engine
        db_module._SessionLocal = testing_session_local
        get_settings().data_dir.mkdir(parents=True, exist_ok=True)
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    get_settings.cache_clear()


@pytest.fixture()
def db_session(client: TestClient) -> Generator[Session, None, None]:
    """Shared DB session bound to the same in-memory engine as the TestClient."""
    import app.db as db_module

    assert db_module._SessionLocal is not None
    session = db_module._SessionLocal()
    try:
        yield session
    finally:
        session.close()


def register_payload(**overrides):
    data = {
        "phone": "+79001112233",
        "email": "athlete@example.com",
        "display_name": "Тест Участник",
        "requested_role": "participant",
        "accept_terms": True,
        "accept_privacy": True,
    }
    data.update(overrides)
    return data


def auth_header(client: TestClient, email: str, role: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/dev-login", json={"email": email, "role": role})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
