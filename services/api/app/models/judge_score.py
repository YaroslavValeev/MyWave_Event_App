"""Judge score sheets for structured scoring."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JudgeScore(Base):
    """One judge sheet for a participant attempt (JSON criteria + computed total)."""

    __tablename__ = "judge_scores"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "participant_id",
            "judge_user_id",
            "attempt_no",
            name="uq_judge_score_sheet",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"),
        index=True,
    )
    heat_id: Mapped[int | None] = mapped_column(
        ForeignKey("heats.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    judge_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    engine: Mapped[str] = mapped_column(String(64), nullable=False)
    # JSON object of criterion -> float
    criteria_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
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
