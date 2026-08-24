"""Competition day entities: Heat, StartListEntry, Run."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Heat(Base):
    """Competition heat (≠ TrainingSlot)."""

    __tablename__ = "heats"
    __table_args__ = (UniqueConstraint("event_id", "code", name="uq_heat_event_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    heat_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # planned | ready | on_water | completed | cancelled
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class StartListEntry(Base):
    """Ordered participant row inside a heat start list."""

    __tablename__ = "start_list_entries"
    __table_args__ = (
        UniqueConstraint("heat_id", "start_order", name="uq_start_list_order"),
        UniqueConstraint("heat_id", "participant_id", name="uq_start_list_participant"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    heat_id: Mapped[int] = mapped_column(ForeignKey("heats.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"),
        index=True,
    )
    start_order: Mapped[int] = mapped_column(Integer, nullable=False)
    bib_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # scheduled | checked_in | ready | on_water | completed | dns | dnf
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    on_water_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Run(Base):
    """Single attempt / run for a start-list entry."""

    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("start_list_entry_id", "attempt_no", name="uq_run_entry_attempt"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    heat_id: Mapped[int] = mapped_column(ForeignKey("heats.id", ondelete="CASCADE"), index=True)
    start_list_entry_id: Mapped[int] = mapped_column(
        ForeignKey("start_list_entries.id", ondelete="CASCADE"),
        index=True,
    )
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"),
        index=True,
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # scheduled | ready | on_water | completed | dns | dnf
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
