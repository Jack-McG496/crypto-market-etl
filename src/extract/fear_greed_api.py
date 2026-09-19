import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config.settings import settings

# reuse retry/dead-letter helpers and exceptions from coingecko client
from src.extract.coingecko_api import (
    PermanentAPIError,
    _do_get,
    _write_dead_letter,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_setting(attr: str, default: Any = None) -> Any:
    value = getattr(settings, attr, default)
    return default if value is None else value


BASE_URL: str | None = _get_setting("FEAR_GREED_API_URL", "https://api.alternative.me/fng")
REQUEST_TIMEOUT: float = _get_setting("FEAR_GREED_REQUEST_TIMEOUT", 10)
RAW_DATA_DIR: Path = Path(_get_setting("RAW_DATA_DIR", "data/raw"))
DEAD_LETTER_DIR: Path = Path(_get_setting("DEAD_LETTER_DIR", "data/dead_letter"))


def _build_url(limit: int) -> str:
    if not BASE_URL:
        raise PermanentAPIError("FEAR_GREED_API_URL not configured")
    return f"{BASE_URL.rstrip('/')}/?limit={limit}&format=json"


def _fg_get(url: str, **kwargs):
    # Use the shared _do_get implementation so the same retry/rate-limit logic applies.
    # Pass a meaningful source key so dead-letter entries reference "fear_greed".
    kwargs.setdefault("coin_id", "fear_greed")
    return _do_get(url, timeout=REQUEST_TIMEOUT, params={}, **kwargs)


def fetch_fear_greed_index(limit: int = 1, run_id: str | None = None) -> dict[str, Any]:
    """
    Fetch Crypto Fear & Greed Index with same retry/backoff/rate-limit/dead-letter behavior
    as the CoinGecko client. Raises PermanentAPIError or TransientAPIError on failure.
    """
    try:
        url = _build_url(limit)
    except PermanentAPIError as exc:
        _write_dead_letter(
            source="fear_greed",
            payload={},
            error=str(exc),
            meta={},
            dead_letter_dir=DEAD_LETTER_DIR,
        )
        raise

    logger = get_logger(__name__, run_id=run_id, stage="extract", task="fetch_fear_greed_index", coin_id="fear_greed")
    logger.info("Fetching Fear & Greed index (limit=%d)", limit)
    result = _fg_get(
        url,
        coin="fear_greed",
        run_id=run_id,
        stage="extract",
        task="fetch_fear_greed_index",
        dead_letter_dir=DEAD_LETTER_DIR,
    )
    logger.info("Fetched Fear & Greed index")
    return result


def save_raw_json(data: Any):
    """
    Save raw API response to data/raw with timestamped filename.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RAW_DATA_DIR / f"fear_greed_index_{timestamp}.json"
    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    logger.info("Raw data saved to %s", file_path)


if __name__ == "__main__":
    try:
        fg = fetch_fear_greed_index(limit=1)
        save_raw_json(fg)
    except PermanentAPIError as exc:
        logger.error("Permanent failure fetching fear & greed index: %s", exc)
    except Exception:
        logger.exception("Unexpected error fetching fear & greed index")
