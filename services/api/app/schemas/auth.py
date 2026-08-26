"""Auth schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.roles import Role


class DevLoginRequest(BaseModel):
    email: EmailStr
    role: Role = Field(default=Role.participant)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    email: str
    user_id: int
    status: str = "active"
    phone: str | None = None
    display_name: str | None = None
    athlete_id: str | None = None


class MeResponse(BaseModel):
    id: int
    email: str
    phone: str | None = None
    role: Role
    requested_role: Role | None = None
    status: str
    display_name: str | None = None
    athlete_id: str | None = None


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, min_length=10, max_length=32)

    @field_validator("display_name")
    @classmethod
    def strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("display_name too short")
        return cleaned


class RegisterRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=32)
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=255)
    requested_role: Role = Field(default=Role.participant)
    accept_terms: bool = False
    accept_privacy: bool = False
    accept_publish_name: bool = False
    accept_analytics: bool = False

    @field_validator("display_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("display_name too short")
        return cleaned


class RegisterResponse(BaseModel):
    user_id: int
    email: str
    phone: str
    role: Role
    requested_role: Role
    status: str
    message: str
    athlete_id: str | None = None
    access_token: str | None = None
    token_type: str | None = None


class PhoneOtpRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=32)


class PhoneOtpResponse(BaseModel):
    ok: bool = True
    phone_masked: str
    message: str
    expires_in_seconds: int
    # Only present in development/test — never rely on this in production clients.
    dev_otp: str | None = None


class PhoneOtpVerifyRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=32)
    code: str = Field(min_length=4, max_length=8)


class RoleDecisionResponse(BaseModel):
    ok: bool
    user_id: int
    email: str
    role: Role
    status: str
    message: str


class PendingApprovalItem(BaseModel):
    approval_id: int
    user_id: int
    email: str
    display_name: str | None
    phone_masked: str | None
    requested_role: Role
    status: str
    created_at: str
    expires_at: str


class PendingApprovalListResponse(BaseModel):
    items: list[PendingApprovalItem]
    total: int
