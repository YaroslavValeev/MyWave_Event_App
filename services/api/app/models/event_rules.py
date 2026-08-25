"""Event rules profile — org, sanction, disciplines, scoring mode."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EventRulesProfile(Base):
    __tablename__ = "event_rules_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    governing_body: Mapped[str] = mapped_column(String(32), nullable=False, default="FVLS")
    sanction_body: Mapped[str] = mapped_column(String(32), nullable=False, default="IWWF")
    # JSON array of discipline codes, e.g. ["wakeboard_cable","wakesurf_boat"]
    discipline_codes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # JSON object discipline_code -> rules_pack_id
    rules_packs_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    scoring_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="photo_protocol")
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
