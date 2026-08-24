"""Consent and legal document schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LegalDocumentOut(BaseModel):
    purpose: str
    title: str
    version: str
    required: bool
    revocable: bool
    summary: str
    body: str | None = None


class LegalDocumentListResponse(BaseModel):
    items: list[LegalDocumentOut]
    current_version: str


class ConsentOut(BaseModel):
    purpose: str
    title: str
    version: str
    required: bool
    revocable: bool
    granted: bool
    granted_at: str | None = None
    current_document_version: str


class ConsentListResponse(BaseModel):
    items: list[ConsentOut]


class ConsentGrantRequest(BaseModel):
    purpose: str = Field(min_length=3, max_length=64)
    version: str | None = Field(default=None, max_length=32)
