"""Immutable official protocol snapshots (ADR-0017)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OfficialProtocolRevision(Base):
    __tablename__ = "official_protocol_revisions"
    __table_args__ = (
        UniqueConstraint("event_id", "revision_no", name="uq_protocol_revision_no"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    # approved only for stored snapshots (immutable)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="approved")
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
