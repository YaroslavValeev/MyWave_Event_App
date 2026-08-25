"""Event schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.event import EventStatus
from app.schemas.rules import EventRulesProfileCreate


class EventCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    city: str | None = Field(default=None, max_length=128)
    location: str | None = Field(default=None, max_length=255)
    venue: str | None = Field(default=None, max_length=255)
    disciplines: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: EventStatus = EventStatus.draft
    rules_profile: EventRulesProfileCreate | None = None


class EventUpdateStatus(BaseModel):
    status: EventStatus


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str | None
    city: str | None = None
    location: str | None = None
    venue: str | None = None
    disciplines: str | None = None
    starts_at: datetime | None
    ends_at: datetime | None
    status: EventStatus
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    items: list[EventRead]
    total: int
