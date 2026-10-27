"""Field moment schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FieldMomentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    heat_id: int | None = None
    title: str
    pov: str
    media_kind: str
    status: str
    file_name: str
    mime_type: str
    byte_size: int
    notes: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime


class FieldMomentListResponse(BaseModel):
    items: list[FieldMomentOut]
    total: int


class FieldMomentUpdate(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(draft|approved|withheld)$")
    notes: str | None = Field(default=None, max_length=4000)
    title: str | None = Field(default=None, max_length=255)
    pov: str | None = Field(default=None, max_length=64)
