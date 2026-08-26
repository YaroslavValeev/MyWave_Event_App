"""Judge scoring schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JudgeScoreSubmit(BaseModel):
    participant_id: int
    heat_id: int | None = None
    attempt_no: int = Field(default=1, ge=1, le=10)
    criteria: dict[str, float]
    notes: str | None = Field(default=None, max_length=2000)
    engine: str | None = Field(default=None, max_length=64)


class JudgeScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    participant_id: int
    heat_id: int | None = None
    judge_user_id: int
    attempt_no: int
    engine: str
    criteria: dict[str, float]
    total: float
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class JudgeScoreListResponse(BaseModel):
    items: list[JudgeScoreOut]
    total: int


class AggregateScoresRequest(BaseModel):
    participant_id: int
    heat_id: int | None = None
    attempt_no: int = Field(default=1, ge=1, le=10)
    write_result_draft: bool = True
    place: int | None = Field(default=None, ge=1)


class AggregateScoresOut(BaseModel):
    engine: str
    panel_score: float
    judge_count: int
    judge_totals: list[float]
    result_id: int | None = None
    detail: dict[str, Any]


class ScoringEngineMetaOut(BaseModel):
    engine: str
    criteria: list[str]
    criteria_labels_ru: dict[str, str]
    aggregation: str
    drop_extremes_if_judges_ge: int | None = None
    best_of_runs: bool = False
    placement_overrides_score: bool = False
