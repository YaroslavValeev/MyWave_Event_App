"""Application settings (env validation via pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_INSECURE_SECRETS = frozenset(
    {
        "change-me-to-a-long-random-string",
        "change-me",
        "secret",
        "changeme",
    }
)

# services/api/app/config.py → services/api → repo root
_API_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _API_DIR.parent.parent

_DEFAULT_CORS = ["http://127.0.0.1:3000", "http://localhost:3000"]


def _split_cors(value: object) -> list[str]:
    if value is None or value == "":
        return list(_DEFAULT_CORS)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    raise TypeError("CORS_ORIGINS must be a comma-separated string or list")


class Settings(BaseSettings):
    """Runtime configuration loaded from environment / .env files."""

    model_config = SettingsConfigDict(
        env_file=(
            str(_REPO_ROOT / ".env"),
            str(_API_DIR / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="MyWave Event App", alias="APP_NAME")
    app_env: Literal["development", "staging", "production", "test"] = Field(
        default="development",
        alias="APP_ENV",
    )
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_public_url: str = Field(default="http://127.0.0.1:8000", alias="API_PUBLIC_URL")
    secret_key: str = Field(default="change-me-to-a-long-random-string", alias="SECRET_KEY")
    # NoDecode: comma-separated env strings must not be JSON-parsed first.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(_DEFAULT_CORS),
        alias="CORS_ORIGINS",
    )
    database_url: str = Field(default="sqlite:///./data/mywave_event.db", alias="DATABASE_URL")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    enable_audit_log: bool = Field(default=True, alias="ENABLE_AUDIT_LOG")
    jwt_access_token_expire_minutes: int = Field(
        default=1440,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    owner_approval_email: str = Field(
        default="y.valeev@gmail.com",
        alias="OWNER_APPROVAL_EMAIL",
    )
    public_web_url: str = Field(
        default="http://127.0.0.1:3000",
        alias="PUBLIC_WEB_URL",
    )
    otp_ttl_minutes: int = Field(default=10, alias="OTP_TTL_MINUTES")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        return _split_cors(value)

    @field_validator("redis_url", mode="before")
    @classmethod
    def empty_redis_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def reject_insecure_production_secret(self):
        if not self.is_production:
            return self
        key = (self.secret_key or "").strip()
        if key in _INSECURE_SECRETS or len(key) < 32:
            raise ValueError(
                "SECRET_KEY must be a unique value of at least 32 characters in production"
            )
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def smtp_configured(self) -> bool:
        return bool((self.smtp_host or "").strip() and (self.smtp_from or "").strip())

    @property
    def otp_challenge_required(self) -> bool:
        """OTP is mandatory in production and whenever email delivery is configured."""
        return self.is_production or self.smtp_configured

    @property
    def repo_root(self) -> Path:
        return _REPO_ROOT

    @property
    def data_dir(self) -> Path:
        return _REPO_ROOT / "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()
