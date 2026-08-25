"""Rules catalog and event rules profile schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.rules_catalog import (
    DEFAULT_GOVERNING_BODY,
    DEFAULT_SANCTION_BODY,
    DEFAULT_SCORING_MODE,
    DISCIPLINES,
    GOVERNING_BODIES,
    P0_DISCIPLINE_CODES,
    SCORING_MODES,
)


class RulesCatalogOut(BaseModel):
    governing_bodies: dict[str, dict[str, str]]
    disciplines: dict[str, dict[str, str]]
    rules_packs: dict[str, dict[str, object]]
    scoring_modes: dict[str, dict[str, str]]
    p0_discipline_codes: list[str]
    defaults: dict[str, str]


class EventRulesProfileCreate(BaseModel):
    governing_body: str = Field(default=DEFAULT_GOVERNING_BODY, max_length=32)
    sanction_body: str = Field(default=DEFAULT_SANCTION_BODY, max_length=32)
    discipline_codes: list[str] = Field(default_factory=list, min_length=1)
    scoring_mode: str = Field(default=DEFAULT_SCORING_MODE, max_length=32)

    @field_validator("discipline_codes")
    @classmethod
    def validate_disciplines(cls, codes: list[str]) -> list[str]:
        unknown = [c for c in codes if c not in DISCIPLINES]
        if unknown:
            raise ValueError(f"unknown discipline codes: {', '.join(unknown)}")
        return codes

    @field_validator("governing_body")
    @classmethod
    def validate_governing(cls, value: str) -> str:
        if value not in GOVERNING_BODIES:
            raise ValueError(f"unknown governing body: {value}")
        return value

    @field_validator("scoring_mode")
    @classmethod
    def validate_scoring_mode(cls, value: str) -> str:
        if value not in SCORING_MODES:
            raise ValueError(f"unknown scoring mode: {value}")
        return value


class EventRulesProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    governing_body: str
    sanction_body: str
    discipline_codes: list[str]
    rules_packs: dict[str, str]
    scoring_mode: str
    created_at: datetime
    updated_at: datetime


class EventRulesProfileUpdate(EventRulesProfileCreate):
    pass
