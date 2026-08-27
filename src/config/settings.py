# settings.py
from __future__ import annotations
import os
import sys
import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, BaseSettings, Field, AnyUrl, ValidationError, validator


class RetryConfig(BaseModel):
    attempts: int = Field(3, ge=0, description="Number of retry attempts (0 = no retries)")
    backoff_factor: float = Field(0.5, ge=0, description="Base backoff multiplier")
    max_backoff_seconds: int = Field(60, ge=0, description="Maximum backoff delay in seconds")
    jitter: bool = Field(True, description="Apply random jitter to backoff")
    strategy: Literal["exponential", "linear", "fixed"] = Field(
        "exponential", description="Backoff strategy"
    )


class Settings(BaseSettings):
    # Environment
    ENV: Literal["development", "staging", "production"] = Field(
        "development", description="Runtime environment"
    )
    FAIL_FAST: bool = Field(True, description="Exit on missing/invalid configuration")

    # External endpoints / keys
    COINGECKO_API_URL: AnyUrl = Field("https://api.coingecko.com/api/v3", description="CoinGecko base URL")
    FEAR_GREED_API_URL: Optional[AnyUrl] = Field(None, description="Fear & Greed index API URL")
    COINGECKO_API_KEY: Optional[str] = Field(None, description="Optional CoinGecko API key")

    # Database
    POSTGRES_DSN: Optional[str] = Field(None, description="Postgres DSN (eg. postgres://user:pass@host/db)")

    # Request / timeout / retry
    REQUEST_TIMEOUT_SECONDS: int = Field(10, ge=0, description="Per-request timeout in seconds")
    RETRY: RetryConfig = Field(default_factory=RetryConfig)

    # RUN ID
    RUN_ID: Optional[str] = Field(None, description="Explicit run id (overrides generation)")
    RUN_ID_GENERATION: Literal["uuid4", "timestamp", "env"] = Field(
        "uuid4",
        description="How to generate `RUN_ID` when `RUN_ID` not provided. 'env' reads RUN_ID from env explicitly.",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("RUN_ID", pre=True, always=True)
    def build_run_id(cls, v, values):
        if v:
            return v
        mode = values.get("RUN_ID_GENERATION", "uuid4")
        if mode == "uuid4":
            return uuid.uuid4().hex
        if mode == "timestamp":
            return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        if mode == "env":
            env_val = os.getenv("RUN_ID")
            if env_val:
                return env_val
            raise ValueError("RUN_ID_GENERATION='env' but environment variable RUN_ID is not set")
        raise ValueError(f"Unsupported RUN_ID_GENERATION: {mode}")


def get_settings() -> Settings:
    """
    Construct Settings with fail-fast behavior:
    - If validation fails and FAIL_FAST is true (default), print errors and exit(1).
    - If FAIL_FAST is false, re-raise the ValidationError for the caller to handle.
    """
    try:
        s = Settings()
        # Example of additional explicit validation: required critical values in production
        if s.ENV == "production":
            missing = []
            if not s.POSTGRES_DSN:
                missing.append("POSTGRES_DSN")
            if not s.COINGECKO_API_KEY:
                # may be optional depending on provider; treat as required in production here
                missing.append("COINGECKO_API_KEY")
            if missing:
                raise ValueError(f"Missing required config in production: {', '.join(missing)}")
        return s
    except ValidationError as exc:
        # pydantic validation error
        print("Configuration validation error:", file=sys.stderr)
        print(exc, file=sys.stderr)
        # decide fail-fast by environment override or default true
        fail_fast = os.getenv("FAIL_FAST", "true").lower() in ("1", "true", "yes")
        if fail_fast:
            sys.exit(1)
        raise
    except Exception as exc:
        print("Configuration error:", file=sys.stderr)
        print(exc, file=sys.stderr)
        fail_fast = os.getenv("FAIL_FAST", "true").lower() in ("1", "true", "yes")
        if fail_fast:
            sys.exit(1)
        raise


# Common pattern: import settings via
# from settings import get_settings
# settings = get_settings()
settings = get_settings()