"""Catalog of Stage 1 legal documents and consent purposes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CURRENT_VERSION = "2026-08-24"

PURPOSE_TERMS = "terms_of_use"
PURPOSE_PRIVACY = "privacy_policy"
PURPOSE_PUBLISH = "publish_name_and_results"
PURPOSE_ANALYTICS = "product_analytics"

REQUIRED_PURPOSES = (PURPOSE_TERMS, PURPOSE_PRIVACY)
OPTIONAL_PURPOSES = (PURPOSE_PUBLISH, PURPOSE_ANALYTICS)
ALL_PURPOSES = REQUIRED_PURPOSES + OPTIONAL_PURPOSES


@dataclass(frozen=True)
class LegalDocument:
    purpose: str
    title: str
    version: str
    required: bool
    revocable: bool
    filename: str | None
    summary: str


CATALOG: dict[str, LegalDocument] = {
    PURPOSE_TERMS: LegalDocument(
        purpose=PURPOSE_TERMS,
        title="Пользовательское соглашение",
        version=CURRENT_VERSION,
        required=True,
        revocable=False,
        filename="terms_of_use.md",
        summary="Правила пользования MyWave Event App.",
    ),
    PURPOSE_PRIVACY: LegalDocument(
        purpose=PURPOSE_PRIVACY,
        title="Политика конфиденциальности",
        version=CURRENT_VERSION,
        required=True,
        revocable=False,
        filename="privacy_policy.md",
        summary="Как обрабатываются персональные данные в приложении.",
    ),
    PURPOSE_PUBLISH: LegalDocument(
        purpose=PURPOSE_PUBLISH,
        title="Публикация имени и результатов",
        version=CURRENT_VERSION,
        required=False,
        revocable=True,
        filename="publish_name_and_results.md",
        summary="Согласие показывать ФИО и результаты в открытом списке события.",
    ),
    PURPOSE_ANALYTICS: LegalDocument(
        purpose=PURPOSE_ANALYTICS,
        title="Продуктовая аналитика",
        version=CURRENT_VERSION,
        required=False,
        revocable=True,
        filename="product_analytics.md",
        summary="Согласие на обезличенные события продукта (без телефона и документов).",
    ),
}


def get_document(purpose: str) -> LegalDocument | None:
    return CATALOG.get(purpose)


def document_body(repo_root: Path, purpose: str) -> str:
    doc = CATALOG.get(purpose)
    if doc is None:
        return ""
    if doc.filename:
        path = repo_root / "docs" / "LEGAL" / doc.filename
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return doc.summary
