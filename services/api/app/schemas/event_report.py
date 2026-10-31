"""EventReport API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventReportOut(BaseModel):
    id: int
    event_id: int
    status: str
    title: str
    body_markdown: str
    facts: dict[str, Any] = Field(default_factory=dict)
    source: str
    created_by_user_id: int | None = None
    updated_by_user_id: int | None = None
    published_by_user_id: int | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventReportUpdate(BaseModel):
    title: str | None = None
    body_markdown: str | None = None


class EventReportAssembleRequest(BaseModel):
    """use_llm=True (default) → AI draft when ENABLE_EVENT_REPORT_LLM; else template."""

    use_llm: bool = True
