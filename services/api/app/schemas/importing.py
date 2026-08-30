"""Import Center API schemas. Phones are masked; no medical URLs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImportRowOut(BaseModel):
    id: int
    source_sheet: str
    source_row: int
    display_name: str | None = None
    phone_masked: str | None = None
    birth_year: int | None = None
    region: str | None = None
    discipline: str | None = None
    category_label: str | None = None
    has_medical: bool = False
    match_kind: str
    confidence: int
    conflict_codes: list[str] = Field(default_factory=list)
    admin_decision: str
    athlete_profile_id: int | None = None
    participant_id: int | None = None


class ImportBatchOut(BaseModel):
    id: int
    event_id: int
    source_filename: str
    source_kind: str
    status: str
    row_count: int
    new_count: int = 0
    exact_count: int = 0
    probable_count: int = 0
    conflict_count: int = 0
    excluded_count: int = 0
    committed_count: int = 0
    created_at: str | None = None
    committed_at: str | None = None
    rows: list[ImportRowOut] | None = None


class ImportBatchListResponse(BaseModel):
    items: list[ImportBatchOut]
    total: int


class ImportRowDecision(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
