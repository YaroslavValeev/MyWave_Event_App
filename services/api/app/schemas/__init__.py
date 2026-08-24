"""Pydantic schemas."""

from app.schemas.auth import (
    DevLoginRequest,
    MeResponse,
    PhoneOtpRequest,
    PhoneOtpResponse,
    PhoneOtpVerifyRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.schemas.common import ErrorResponse
from app.schemas.event import EventCreate, EventListResponse, EventRead, EventUpdateStatus
from app.schemas.health import HealthResponse, ReadyResponse

__all__ = [
    "DevLoginRequest",
    "MeResponse",
    "PhoneOtpRequest",
    "PhoneOtpResponse",
    "PhoneOtpVerifyRequest",
    "RegisterRequest",
    "RegisterResponse",
    "TokenResponse",
    "ErrorResponse",
    "EventCreate",
    "EventListResponse",
    "EventRead",
    "EventUpdateStatus",
    "HealthResponse",
    "ReadyResponse",
]
