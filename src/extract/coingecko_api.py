import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable

import requests

from src.utils.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)

# Exceptions
class TransientAPIError(Exception):
    pass


class PermanentAPIError(Exception):
    pass


def _get_setting(attr: str, default: Any = None) -> Any:
    return getattr(settings, attr, default)


# Backwards-compatible config extraction (older code referenced different names)
BASE_URL: str = _get_setting("COINGECKO_API_URL", _get_setting("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3"))
API_KEY: Optional[str] = _get_setting("COINGECKO_API_KEY", None)
REQUEST_TIMEOUT: float = _get_setting("REQUEST_TIMEOUT_SECONDS", _get_setting("COINGECKO_REQUEST_TIMEOUT", 10))
REQUEST_PARAMS: Dict[str, Any] = _get_setting("COINGECKO_REQUEST_PARAMETERS", {})
RAW_DATA_DIR: Path = Path(_get_setting("RAW_DATA_DIR", "data/raw"))
DEAD_LETTER_DIR: Path = Path(_get_setting("DEAD_LETTER_DIR", "data/dead_letter"))
COINS = _get_setting("COIN_LIST", [])
RETRY_CFG = _get_setting("RETRY", None)
if RETRY_CFG is None:
    # default mirror of settings.RetryConfig
    RETRY_CFG = {
        "attempts": 3,
        "backoff_factor": 0.5,
        "max_backoff_seconds": 60,
        "jitter": True,
        "strategy": "exponential",
    }


def _compute_backoff(attempt: int) -> float:
    attempts = int(RETRY_CFG.get("attempts", 3))
    factor = float(RETRY_CFG.get("backoff_factor", 0.5))
    max_backoff = float(RETRY_CFG.get("max_backoff_seconds", 60))
    jitter = bool(RETRY_CFG.get("jitter", True))
    strategy = RETRY_CFG.get("strategy", "exponential")

    if strategy == "fixed":
        backoff = factor
    elif strategy == "linear":
        backoff = factor * attempt
    else:  # exponential
        backoff = factor * (2 ** (attempt - 1))

    backoff = min(backoff, max_backoff)
    if jitter:
        backoff = random.uniform(0, backoff)
    return backoff


def _is_rate_limited(resp: requests.Response) -> bool:
    return resp.status_code == 429


def _get_retry_after_seconds(resp: requests.Response) -> Optional[float]:
    header = resp.headers.get("Retry-After")
    if not header:
        return None
    try:
        # sometimes integer seconds
        return float(header)
    except ValueError:
        # or an HTTP-date; try parse RFC 2822-ish by using requests' parsing via email.utils
        try:
            from email.utils import parsedate_to_datetime

            dt = parsedate_to_datetime(header)
            delta = (dt - datetime.utcnow()).total_seconds()
            return max(delta, 0)
        except Exception:
            return None


def _write_dead_letter(
    source: str,
    payload: Any,
    error: str,
    meta: Optional[Dict[str, Any]] = None,
    stage: str = "unknown",
    run_id: Optional[str] = None,
) -> None:
    DEAD_LETTER_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{source}_deadletter_{timestamp}.json"
    path = DEAD_LETTER_DIR / filename
    body = {
        "source": source,
        "stage": stage,
        "timestamp_utc": timestamp,
        "error": error,
        "meta": meta or {},
        "payload": payload,
        "run_id": run_id,
    }
    try:
        with path.open("w", encoding="utf-8") as fh:
            json.dump(body, fh, indent=2, default=str)
        logger.warning("Wrote dead-letter to %s", path)
    except Exception as exc:
        logger.exception("Failed to write dead-letter file: %s", exc)

    # Optional: try writing to DB if POSTGRES_DSN is configured
    dsn = _get_setting("POSTGRES_DSN", None)
    if dsn:
        try:
            import psycopg2
            from psycopg2.extras import Json

            conn = psycopg2.connect(dsn)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS dead_letter_events (
                            id SERIAL PRIMARY KEY,
                            source TEXT NOT NULL,
                            stage TEXT NOT NULL,
                            payload JSONB NOT NULL,
                            error TEXT NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                            run_id TEXT
                        )
                        """
                    )
                    cur.execute(
                        "INSERT INTO dead_letter_events (source, stage, payload, error, run_id) VALUES (%s, %s, %s, %s, %s)",
                        (source, stage, Json(payload), error, run_id),
                    )
            conn.close()
            logger.warning("Inserted dead-letter into DB (dead_letter_events)")
        except Exception:
            logger.exception("Failed to write dead-letter to DB; file already created as fallback.")


def retry_and_handle_rate_limits(func: Callable[..., requests.Response]) -> Callable[..., Any]:
    def wrapper(*args, **kwargs):
        attempts = int(RETRY_CFG.get("attempts", 3))
        last_exc: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            try:
                resp = func(*args, **kwargs)

                # If rate-limited, attempt to honor Retry-After and retry (classify as transient)
                if _is_rate_limited(resp):
                    retry_after = _get_retry_after_seconds(resp)
                    delay = retry_after if retry_after is not None else _compute_backoff(attempt)
                    logger.warning("Rate limited (429). Retry-After=%s; sleeping %.2fs", retry_after, delay)
                    time.sleep(delay)
                    raise TransientAPIError(f"Rate limited: {resp.status_code}")

                # 5xx -> transient
                if 500 <= resp.status_code < 600:
                    logger.warning("Server error %s on attempt %d", resp.status_code, attempt)
                    raise TransientAPIError(f"Server error: {resp.status_code}")

                # 4xx (except 429) -> permanent (client error)
                if 400 <= resp.status_code < 500:
                    logger.error("Client error %s; classifying as permanent", resp.status_code)
                    # try to include body for dead-letter
                    try:
                        body = resp.json()
                    except Exception:
                        body = resp.text
                    _write_dead_letter(
                        source=kwargs.get("coin_id", kwargs.get("coin", "coingecko")),
                        payload=body,
                        error=f"HTTP {resp.status_code}",
                        meta={"status_code": resp.status_code, "url": resp.url},
                        stage="api",
                    )
                    raise PermanentAPIError(f"Permanent HTTP error: {resp.status_code}")

                # success
                resp.raise_for_status()
                try:
                    return resp.json()
                except ValueError:
                    return resp.text

            except PermanentAPIError:
                raise
            except TransientAPIError as exc:
                last_exc = exc
                if attempt == attempts:
                    logger.error("Exhausted retries due to transient error: %s", exc)
                    raise
                backoff = _compute_backoff(attempt)
                logger.info("Transient error, attempt %d/%d — backing off %.2fs", attempt, attempts, backoff)
                time.sleep(backoff)
                continue
            except requests.exceptions.RequestException as exc:
                last_exc = exc
                # classify some request exceptions as transient
                transient = isinstance(
                    exc,
                    (
                        requests.exceptions.Timeout,
                        requests.exceptions.ConnectionError,
                        requests.exceptions.ChunkedEncodingError,
                        requests.exceptions.ContentDecodingError,
                    ),
                )
                if transient:
                    if attempt == attempts:
                        logger.exception("Network/transient error, exhausted retries")
                        raise TransientAPIError(str(exc)) from exc
                    backoff = _compute_backoff(attempt)
                    logger.info("Network error (%s). attempt %d/%d — sleeping %.2fs", type(exc).__name__, attempt, attempts, backoff)
                    time.sleep(backoff)
                    continue
                # treat other request exceptions as permanent
                logger.exception("Non-transient request exception; writing dead-letter and failing")
                _write_dead_letter(
                    source=kwargs.get("coin_id", kwargs.get("coin", "coingecko")),
                    payload={},
                    error=str(exc),
                    meta={},
                )
                raise PermanentAPIError(str(exc)) from exc

        # if we get here, re-raise last exception
        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected error in retry wrapper")

    return wrapper


@retry_and_handle_rate_limits
def _do_get(url: str, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {}) or {}
    if API_KEY:
        headers.setdefault("x-cg-pro-api-key", API_KEY)
    timeout = kwargs.pop("timeout", REQUEST_TIMEOUT)
    params = kwargs.pop("params", REQUEST_PARAMS)
    return requests.get(url, headers=headers, params=params, timeout=timeout, **kwargs)


def fetch_coin_market_data(coin_id: str) -> Dict[str, Any]:
    """
    Fetch current market data from CoinGecko, with retries, rate-limit handling,
    transient/permanent classification, and dead-letter writes for permanent failures.
    Raises TransientAPIError (after retries) or PermanentAPIError.
    """
    url = f"{BASE_URL.rstrip('/')}/coins/{coin_id}"
    logger.info("Fetching CoinGecko market data for %s", coin_id)
    result = _do_get(url, coin_id=coin_id)
    logger.info("Fetched CoinGecko market data for %s", coin_id)
    return result


def save_raw_json(data: Any, source_name: str):
    """
    Save raw API response to data/raw with timestamped filename.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RAW_DATA_DIR / f"{source_name}_market_data_{timestamp}.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Raw data saved to %s", file_path)


# Convenience CLI usage
if __name__ == "__main__":
    for coin in COINS:
        try:
            raw_data = fetch_coin_market_data(coin)
            save_raw_json(raw_data, source_name=f"coingecko_{coin}")
        except PermanentAPIError as exc:
            logger.error("Permanent failure fetching %s: %s", coin, exc)
        except Exception:
            logger.exception("Unexpected error for coin %s", coin)