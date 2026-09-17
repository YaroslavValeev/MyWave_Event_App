"""Import Center staging tables — PII lives in DB only, never in git."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ImportBatch(Base):
    __tablename__ = "import_batches"
    __table_args__ = (UniqueConstraint("event_id", "content_sha256", name="uq_import_event_sha"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="parsed")
    uploaded_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exact_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    probable_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflict_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    excluded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    committed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImportRow(Base):
    __tablename__ = "import_rows"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id", ondelete="CASCADE"), index=True)
    source_sheet: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    normalized_fio: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latin_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_e164: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discipline: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    has_medical: Mapped[bool] = mapped_column(default=False, nullable=False)
    match_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflict_codes: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    athlete_profile_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    admin_decision: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    decided_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    participant_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
