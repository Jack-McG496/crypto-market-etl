# settings.py
from __future__ import annotations
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

try:
    # pydantic v2 moved BaseSettings to pydantic-settings package
    from pydantic import BaseModel, Field, AnyUrl, ValidationError
    from pydantic_settings import BaseSettings
except Exception:
    from pydantic import BaseModel, BaseSettings, Field, AnyUrl, ValidationError


class RetryConfig(BaseModel):
    attempts: int = Field(3, ge=0, description="Number of retry attempts (0 = no retries)")
    backoff_factor: float = Field(0.5, ge=0, description="Base backoff multiplier")
    max_backoff_seconds: int = Field(60, ge=0, description="Maximum backoff delay in seconds")
    jitter: bool = Field(True, description="Apply random jitter to backoff")
    strategy: Literal["exponential", "linear", "fixed"] = Field(
        "exponential", description="Backoff strategy"
    )


class Settings(BaseSettings):
    # keep Config for compatibility; ignore unknown env keys
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
    # Convenience fields used across the codebase (may be derived from POSTGRES_DSN)
    DB_HOST: Optional[str] = Field(None, description="Postgres host")
    DB_PORT: Optional[int] = Field(None, description="Postgres port")
    DB_NAME: Optional[str] = Field(None, description="Postgres database name")
    DB_USER: Optional[str] = Field(None, description="Postgres user")
    DB_PASSWORD: Optional[str] = Field(None, description="Postgres password")

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
        extra = "ignore"
        case_sensitive = False
        


def get_settings() -> Settings:
    """
    Construct Settings with fail-fast behavior:
    - If validation fails and FAIL_FAST is true (default), print errors and exit(1).
    - If FAIL_FAST is false, re-raise the ValidationError for the caller to handle.
    """
    try:
        s = Settings()
        # Ensure RUN_ID is populated according to RUN_ID_GENERATION if not provided
        if not s.RUN_ID:
            mode = s.RUN_ID_GENERATION or "uuid4"
            if mode == "uuid4":
                s.RUN_ID = uuid.uuid4().hex
            elif mode == "timestamp":
                s.RUN_ID = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            elif mode == "env":
                env_val = os.getenv("RUN_ID")
                if env_val:
                    s.RUN_ID = env_val
                else:
                    raise ValueError("RUN_ID_GENERATION='env' but environment variable RUN_ID is not set")
            else:
                raise ValueError(f"Unsupported RUN_ID_GENERATION: {mode}")
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

        # Populate DB_* convenience fields from POSTGRES_DSN or environment variables
        try:
            if s.POSTGRES_DSN:
                # parse DSN like: postgres://user:pass@host:port/dbname
                from urllib.parse import urlparse

                parsed = urlparse(s.POSTGRES_DSN)
                if not s.DB_HOST:
                    s.DB_HOST = parsed.hostname
                if not s.DB_PORT and parsed.port:
                    s.DB_PORT = parsed.port
                if not s.DB_USER:
                    s.DB_USER = parsed.username
                if not s.DB_PASSWORD:
                    s.DB_PASSWORD = parsed.password
                if not s.DB_NAME and parsed.path:
                    s.DB_NAME = parsed.path.lstrip("/")

            # fallback to environment variables if still missing
            s.DB_HOST = s.DB_HOST or os.getenv("DB_HOST")
            s.DB_PORT = s.DB_PORT or (int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None)
            s.DB_NAME = s.DB_NAME or os.getenv("DB_NAME")
            s.DB_USER = s.DB_USER or os.getenv("DB_USER")
            s.DB_PASSWORD = s.DB_PASSWORD or os.getenv("DB_PASSWORD")
        except Exception:
            # non-fatal: let callers handle missing DB fields; don't crash here
            pass
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

# Backwards-compatible module-level exports (so callers can `from src.config.settings import DB_HOST`)
DB_HOST = settings.DB_HOST or os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST")
DB_PORT = settings.DB_PORT or (int(os.getenv("POSTGRES_PORT")) if os.getenv("POSTGRES_PORT") else None) or os.getenv("DB_PORT")
DB_NAME = settings.DB_NAME or os.getenv("POSTGRES_DB") or os.getenv("DB_NAME")
DB_USER = settings.DB_USER or os.getenv("POSTGRES_USER") or os.getenv("DB_USER")
DB_PASSWORD = settings.DB_PASSWORD or os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")
POSTGRES_DSN = settings.POSTGRES_DSN

COINGECKO_API_URL = getattr(settings, "COINGECKO_API_URL", None)
COINGECKO_BASE_URL = COINGECKO_API_URL
COINGECKO_API_KEY = getattr(settings, "COINGECKO_API_KEY", None)
REQUEST_TIMEOUT_SECONDS = getattr(settings, "REQUEST_TIMEOUT_SECONDS", None)
RETRY = getattr(settings, "RETRY", None)

# CoinGecko / rate limit tuning
COINGECKO_REQUEST_TIMEOUT = getattr(settings, "COINGECKO_REQUEST_TIMEOUT", REQUEST_TIMEOUT_SECONDS or 10)
# How long to sleep between API calls to avoid hitting provider rate limits
RATE_LIMIT_SLEEP_TIME = getattr(settings, "RATE_LIMIT_SLEEP_TIME", 1)

# Useful directories & lists (may be defined in settings or fallback to defaults)
RAW_DATA_DIR = Path(getattr(settings, "RAW_DATA_DIR", "data/raw"))
PROCESSED_DATA_DIR = Path(getattr(settings, "PROCESSED_DATA_DIR", "data/processed"))
# default coin list for local dev/backfill when not provided via env or config
COIN_LIST = getattr(settings, "COIN_LIST", ["bitcoin", "ethereum"])
BACKFILL_DAYS = getattr(settings, "BACKFILL_DAYS", 7)

# Logging / notifications
LOG_DIR = Path(getattr(settings, "LOG_DIR", "logs"))
LOG_FILE = getattr(settings, "LOG_FILE", "app.log")
SLACK_WEBHOOK_URL = getattr(settings, "SLACK_WEBHOOK_URL", None)
SLACK_TIMEOUT = getattr(settings, "SLACK_TIMEOUT", 5)

# Thresholds / tuning
ANOMALY_DETECTION_THRESHOLD = getattr(settings, "ANOMALY_DETECTION_THRESHOLD", None)