"""Database engine and session helpers."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _make_engine(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(database_url, connect_args=connect_args, future=True)


def init_db(settings: Settings | None = None) -> None:
    """Create engine, ensure data dir, and create tables."""
    global _engine, _SessionLocal

    settings = settings or get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / ".gitkeep").touch(exist_ok=True)

    _engine = _make_engine(settings.database_url)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)

    from app.models import Base  # noqa: WPS433 — late import after engine ready

    Base.metadata.create_all(bind=_engine)
    _ensure_sqlite_columns(_engine, settings.database_url)


def _ensure_sqlite_columns(engine, database_url: str) -> None:
    """Best-effort ALTER for Stage-1 SQLite without Alembic."""
    if not database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(participants)")).fetchall()
        }
        if "user_id" not in cols:
            conn.execute(text("ALTER TABLE participants ADD COLUMN user_id INTEGER"))
        if "phone" not in cols:
            conn.execute(text("ALTER TABLE participants ADD COLUMN phone VARCHAR(32)"))
        if "has_medical_cert" not in cols:
            conn.execute(
                text("ALTER TABLE participants ADD COLUMN has_medical_cert BOOLEAN DEFAULT 0 NOT NULL")
            )
        if "medical_cert_url" not in cols:
            conn.execute(text("ALTER TABLE participants ADD COLUMN medical_cert_url VARCHAR(1024)"))
        if "athlete_profile_id" not in cols:
            conn.execute(text("ALTER TABLE participants ADD COLUMN athlete_profile_id INTEGER"))

        event_cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(events)")).fetchall()
        }
        if event_cols:
            if "roster_locked_at" not in event_cols:
                conn.execute(text("ALTER TABLE events ADD COLUMN roster_locked_at DATETIME"))
            if "roster_locked_by_user_id" not in event_cols:
                conn.execute(text("ALTER TABLE events ADD COLUMN roster_locked_by_user_id INTEGER"))

        user_cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()
        }
        if "athlete_id" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN athlete_id VARCHAR(32)"))
            conn.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_athlete_id ON users (athlete_id)")
            )

        doc_cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(documents)")).fetchall()
        }
        if doc_cols:
            if "access_class" not in doc_cols:
                conn.execute(
                    text("ALTER TABLE documents ADD COLUMN access_class VARCHAR(32) DEFAULT 'public' NOT NULL")
                )
            if "content_sha256" not in doc_cols:
                conn.execute(text("ALTER TABLE documents ADD COLUMN content_sha256 VARCHAR(64)"))
            if "superseded_by_id" not in doc_cols:
                conn.execute(text("ALTER TABLE documents ADD COLUMN superseded_by_id INTEGER"))


def get_engine():
    if _engine is None:
        init_db()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    if _SessionLocal is None:
        init_db()
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def check_db() -> bool:
    """Return True if a simple SELECT 1 succeeds."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
