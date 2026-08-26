"""Official protocol export bundle schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OfficialProtocolReadiness(BaseModel):
    official_ready: bool = False
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    published_results_count: int = 0
    published_protocol_captures_count: int = 0


class OfficialProtocolBundle(BaseModel):
    format_version: str = "1.0"
    generated_at: datetime
    generator: str
    event: dict[str, Any]
    rules_profile: dict[str, Any] | None = None
    scoring_engine: str | None = None
    officials: list[dict[str, Any]] = Field(default_factory=list)
    categories: list[dict[str, Any]] = Field(default_factory=list)
    participants: list[dict[str, Any]] = Field(default_factory=list)
    heats: list[dict[str, Any]] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)
    protocol_captures: list[dict[str, Any]] = Field(default_factory=list)
    judge_scores: list[dict[str, Any]] = Field(default_factory=list)
    readiness: OfficialProtocolReadiness
