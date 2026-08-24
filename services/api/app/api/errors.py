"""Structured API error helpers."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def error_payload(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def raise_api_error(status_code: int, code: str, message: str) -> None:
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        payload = error_payload(str(detail["code"]), str(detail["message"]))
    elif isinstance(detail, str):
        payload = error_payload("http_error", detail)
    else:
        payload = error_payload("http_error", str(detail))
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    messages = "; ".join(
        f"{'.'.join(str(p) for p in err.get('loc', []))}: {err.get('msg')}" for err in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content=error_payload("validation_error", messages or "Validation failed"),
    )
