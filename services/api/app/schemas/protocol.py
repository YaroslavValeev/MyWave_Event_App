"""Protocol capture (photo/PDF judge sheet) schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProtocolCaptureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    heat_id: int | None = None
    title: str
    kind: str
    status: str
    file_name: str
    mime_type: str
    notes: str | None = None
    extracted: dict[str, Any] | None = None
    created_by_user_id: int | None = None
    verified_by_user_id: int | None = None
    verified_at: datetime | None = None
    created_at: datetime


class ProtocolCaptureListResponse(BaseModel):
    items: list[ProtocolCaptureOut]
    total: int


class ProtocolCaptureUpdate(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(draft|verified|published|rejected)$")
    notes: str | None = Field(default=None, max_length=4000)
    extracted: dict[str, Any] | None = None
    title: str | None = Field(default=None, max_length=255)
