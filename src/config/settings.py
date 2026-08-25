from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip() or None

def _get_int_env(name: str, default: int) -> int:
    value = _get_env(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got: {value}") from exc

REQUIRED_ENVS = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
]

def validate_settings(raise_on_missing: bool = True) -> list[str]:
    missing = []
    for name in REQUIRED_ENVS:
        if _get_env(name) is None:
            missing.append(name)
    if missing and raise_on_missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")
    return missing

# Run validation at import-time in non-test flows (CI/tests may override)
try:
    validate_settings()
except RuntimeError:
    # allow tests/CI to import settings then override envs; re-raise only in production runs
    if not (("pytest" in os.getenv("_", "") or "PYTEST_CURRENT_TEST" in os.environ) or os.getenv("CI")):
        raise

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "etl.log"
LOG_LEVEL = _get_env("LOG_LEVEL") or "INFO"
RUN_ID = _get_env("RUN_ID")

# Database
DB_HOST = _get_env("POSTGRES_HOST", "localhost")
DB_PORT = _get_int_env("POSTGRES_PORT", 5432)
DB_NAME = _get_env("POSTGRES_DB", "crypto_db")
DB_USER = _get_env("POSTGRES_USER", "crypto")
DB_PASSWORD = _get_env("POSTGRES_PASSWORD", "crypto")

# CoinGecko
COINGECKO_API_KEY = _get_env("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_REQUEST_TIMEOUT = int(_get_env("COINGECKO_REQUEST_TIMEOUT") or 30)
COINGECKO_REQUEST_RETRIES = int(_get_env("COINGECKO_REQUEST_RETRIES") or 3)
COINGECKO_BACKOFF_BASE = float(_get_env("COINGECKO_BACKOFF_BASE") or 2)
COINGECKO_REQUEST_PARAMETERS = {
    "localization": "false",
    "tickers": "false",
    "market_data": "true",
    "community_data": "false",
    "developer_data": "false",
    "sparkline": "false",
}
COIN_LIST = ["bitcoin", "ethereum"]
BACKFILL_DAYS = 90
RATE_LIMIT_SLEEP_TIME = float(_get_env("RATE_LIMIT_SLEEP_TIME") or 1.5)

# Fear & Greed
FEAR_GREED_API_URL = "https://api.alternative.me/fng/"
FEAR_GREED_REQUEST_TIMEOUT = int(_get_env("FEAR_GREED_REQUEST_TIMEOUT") or 30)

# Analytics
ANOMALY_DETECTION_THRESHOLD = 3.0

# Notifications
SLACK_WEBHOOK_URL = _get_env("SLACK_WEBHOOK_URL")
SLACK_TIMEOUT = int(_get_env("SLACK_TIMEOUT") or 10)