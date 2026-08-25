"""Rules catalog API."""

from __future__ import annotations

from fastapi import APIRouter

from app.domain.rules_catalog import catalog_payload
from app.schemas.rules import RulesCatalogOut

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/catalog", response_model=RulesCatalogOut)
def rules_catalog() -> RulesCatalogOut:
    return RulesCatalogOut.model_validate(catalog_payload())
