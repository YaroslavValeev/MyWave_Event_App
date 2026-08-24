"""Category / participant / document schemas."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    code: str
    title: str
    discipline: str | None = None
    notes: str | None = None
    created_at: datetime


class ParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    category_id: int | None = None
    user_id: int | None = None
    full_name: str
    gender: str | None = None
    birth_year: int | None = None
    club: str | None = None
    region: str | None = None
    city: str | None = None
    federation: str | None = None
    # Public bool only — never expose medical_cert_url here.
    has_medical_cert: bool = False
    status: str
    created_at: datetime


class ApplicationCreate(BaseModel):
    category_id: int | None = None
    club: str | None = Field(default=None, max_length=255)
    region: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=128)
    gender: str | None = Field(default=None, max_length=32)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)


class ApplicationDecision(BaseModel):
    status: str = Field(..., pattern=r"^(accepted|rejected)$")


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    category_id: int | None = None
    user_id: int | None = None
    full_name: str
    club: str | None = None
    region: str | None = None
    city: str | None = None
    gender: str | None = None
    birth_year: int | None = None
    status: str
    created_at: datetime


class ApplicationListResponse(BaseModel):
    items: list[ApplicationOut]
    total: int


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    title: str
    kind: str
    language: str | None = None
    file_name: str
    description: str | None = None
    created_at: datetime


class EventDetailOut(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None = None
    city: str | None = None
    location: str | None = None
    venue: str | None = None
    disciplines: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    categories_count: int = 0
    participants_count: int = 0
    documents_count: int = 0
    officials_count: int = 0
    training_slots_count: int = 0


class ParticipantListResponse(BaseModel):
    items: list[ParticipantOut]
    total: int


class CategoryListResponse(BaseModel):
    items: list[CategoryOut]
    total: int


class DocumentListResponse(BaseModel):
    items: list[DocumentOut]
    total: int


class OfficialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    sort_order: int
    full_name: str
    position: str
    region: str | None = None
    judge_category: str | None = None
    notes: str | None = None
    user_id: int | None = None
    created_at: datetime


class OfficialListResponse(BaseModel):
    items: list[OfficialOut]
    total: int


class TrainingSlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    discipline: str
    venue: str | None = None
    slot_date: date
    slot_time: str | None = None
    status: str
    athlete_name: str | None = None
    notes: str | None = None
    sort_order: int

    @field_validator("slot_time", mode="before")
    @classmethod
    def _time_to_str(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, time):
            return value.strftime("%H:%M")
        text = str(value)
        if len(text) >= 5 and text[2] == ":":
            return text[:5]
        return text


class TrainingSlotListResponse(BaseModel):
    items: list[TrainingSlotOut]
    total: int


class ScheduleHint(BaseModel):
    summary: str
    notes: list[str] = Field(default_factory=list)
