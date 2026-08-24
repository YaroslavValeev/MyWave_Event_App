"""Official training slots (practice schedule)."""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TrainingSlot(Base):
    __tablename__ = "training_slots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    discipline: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    slot_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open")
    athlete_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
