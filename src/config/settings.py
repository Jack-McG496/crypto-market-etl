import os
from pathlib import Path

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


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "etl.log"

# Database
DB_HOST = _get_env("POSTGRES_HOST", "localhost")
DB_PORT = _get_int_env("POSTGRES_PORT", 5432)
DB_NAME = _get_env("POSTGRES_DB", "crypto_db")
DB_USER = _get_env("POSTGRES_USER", "crypto")
DB_PASSWORD = _get_env("POSTGRES_PASSWORD", "crypto")

# CoinGecko
COINGECKO_API_KEY = _get_env("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_REQUEST_TIMEOUT = 30
COINGECKO_REQUEST_RETRIES = 3
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
RATE_LIMIT_SLEEP_TIME = 1.5

# Fear & Greed
FEAR_GREED_API_URL = "https://api.alternative.me/fng/"
FEAR_GREED_REQUEST_TIMEOUT = 30

# Analytics
ANOMALY_DETECTION_THRESHOLD = 3.0

# Notifications
SLACK_WEBHOOK_URL = _get_env("SLACK_WEBHOOK_URL")
SLACK_TIMEOUT = 10