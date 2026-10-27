"""Schemas for the app download catalog and analytics ingest."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AppDownloadAppOut(BaseModel):
    id: str
    name: str
    short_description: str
    features: list[str]
    version: str
    last_updated: str
    platforms: list[str]
    readiness: str
    available_count: int


class AppDownloadArtifactOut(BaseModel):
    id: str
    label: str
    platform: str
    format: str
    version: str
    size: str | None = None
    last_updated: str
    action_label: str
    requirements: list[str]
    state: str
    message: str


class AppDownloadManifestOut(BaseModel):
    app: AppDownloadAppOut
    artifacts: list[AppDownloadArtifactOut]
    generated_at: str


class AppDownloadHandoffOut(BaseModel):
    artifact_id: str
    location: str
    open_in_new_tab: bool
    message: str


class AnalyticsEventIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event: str = Field(min_length=1, max_length=80)
    context: str | None = Field(default=None, max_length=120)
    channel: str | None = Field(default="web", max_length=40)
    properties: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


class AnalyticsEventAccepted(BaseModel):
    accepted: bool = True
    event: str
