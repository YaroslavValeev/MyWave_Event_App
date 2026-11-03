"""Pydantic schemas for event publications."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PublicationType = Literal["post", "news"]
PublicationStatus = Literal[
    "draft",
    "pending_moderation",
    "published",
    "rejected",
    "void",
]


class PublicationMediaOut(BaseModel):
    id: int
    file_name: str
    mime_type: str
    file_size: int
    sort_order: int
    download_path: str

    model_config = {"from_attributes": True}


class PublicationOut(BaseModel):
    id: int
    event_id: int
    author_user_id: int | None
    author_role: str
    author_display_name: str
    type: PublicationType
    title: str
    body: str
    status: PublicationStatus
    version: int
    moderation_note: str | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    media: list[PublicationMediaOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PublicationListResponse(BaseModel):
    items: list[PublicationOut]
    total: int


class PublicationCreate(BaseModel):
    type: PublicationType = "post"
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(default="", max_length=20000)
    author_role: str = Field(min_length=2, max_length=64)
    # draft | publish (publish may become pending_moderation)
    intent: Literal["draft", "publish"] = "draft"
    idempotency_key: str | None = Field(default=None, max_length=128)


class PublicationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = Field(default=None, max_length=20000)
    type: PublicationType | None = None


class PublicationModerate(BaseModel):
    action: Literal["publish", "reject", "void"]
    note: str | None = Field(default=None, max_length=512)
