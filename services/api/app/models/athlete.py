"""Athlete profile — SoT for MyWave Athlete ID (no phone/FIO encoded in the ID)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AthleteProfile(Base):
    __tablename__ = "athlete_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    athlete_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latin_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AthleteContact(Base):
    __tablename__ = "athlete_contacts"
    __table_args__ = (UniqueConstraint("athlete_profile_id", "phone_e164", name="uq_athlete_contact_phone"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    athlete_profile_id: Mapped[int] = mapped_column(
        ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phone_e164: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="self")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AccountAthleteLink(Base):
    """One login account may claim several athletes (guardian / self)."""

    __tablename__ = "account_athlete_links"
    __table_args__ = (
        UniqueConstraint("user_id", "athlete_profile_id", name="uq_account_athlete"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    athlete_profile_id: Mapped[int] = mapped_column(
        ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation: Mapped[str] = mapped_column(String(32), nullable=False, default="self")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_claim")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
