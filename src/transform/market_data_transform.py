from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import json
import pandas as pd

from src.utils.logger import get_logger
from src.config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR, settings
from src.extract.coingecko_api import _write_dead_letter

logger = get_logger(__name__)


class InvalidRawDataError(Exception):
    pass


def load_latest_coingecko_file(coin: str) -> Tuple[Dict[str, Any], Path]:
    """
    Load the latest raw CoinGecko JSON file for a given coin.
    Returns tuple (parsed_json, file_path)
    """
    files = sorted(RAW_DATA_DIR.glob(f"coingecko_{coin}_*.json"), reverse=True)

    if not files:
        raise FileNotFoundError(f"No raw files found for {coin}")

    path = files[0]
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data, path


def _is_valid_number(v: Any) -> bool:
    try:
        return v is not None and float(v) == float(v) and not (float(v) == float("inf"))
    except Exception:
        return False


def transform_market_data(raw_data: Dict[str, Any], source_file: Optional[Path] = None, run_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Transform raw CoinGecko JSON into a flat dict with validation and metadata.
    Raises InvalidRawDataError (and writes dead-letter) on permanent validation failures.
    """
    required_top = ("id", "symbol", "name", "market_data")
    missing = [k for k in required_top if k not in raw_data]
    if missing:
        error = f"Missing top-level keys: {missing}"
        _write_dead_letter(source=raw_data.get("id", "unknown"), payload=raw_data, error=error, meta={"source_file": str(source_file) if source_file else None})
        raise InvalidRawDataError(error)

    market = raw_data.get("market_data", {})
    # required nested fields
    try:
        price_usd = market["current_price"]["usd"]
        market_cap_usd = market["market_cap"]["usd"]
        total_volume_usd = market["total_volume"]["usd"]
        circulating_supply = market.get("circulating_supply")
    except Exception as exc:
        error = f"Missing nested market_data fields: {exc}"
        _write_dead_letter(source=raw_data.get("id", "unknown"), payload=raw_data, error=error, meta={"source_file": str(source_file) if source_file else None})
        raise InvalidRawDataError(error)

    # validate numeric values
    if not (_is_valid_number(price_usd) and _is_valid_number(market_cap_usd) and _is_valid_number(total_volume_usd)):
        error = "One or more numeric market fields are invalid"
        _write_dead_letter(source=raw_data.get("id", "unknown"), payload=raw_data, error=error, meta={"source_file": str(source_file) if source_file else None})
        raise InvalidRawDataError(error)

    # safe computations
    price_usd_f = float(price_usd)
    market_cap_f = float(market_cap_usd)
    total_volume_f = float(total_volume_usd)

    if market_cap_f == 0:
        volume_to_marketcap = None
    else:
        volume_to_marketcap = total_volume_f / market_cap_f

    # price change percent may be missing; guard use
    price_change_24h_pct = market.get("price_change_percentage_24h")
    try:
        price_change_24h_pct = float(price_change_24h_pct) if price_change_24h_pct is not None else None
    except Exception:
        price_change_24h_pct = None

    ingestion_ts = datetime.utcnow()

    out = {
        "coin_id": raw_data["id"],
        "symbol": raw_data["symbol"],
        "name": raw_data["name"],
        "timestamp_utc": ingestion_ts,
        "price_usd": price_usd_f,
        "market_cap_usd": market_cap_f,
        "total_volume_usd": total_volume_f,
        "circulating_supply": circulating_supply,
        "price_change_24h_pct": price_change_24h_pct,
        # additional derived & guarded fields
        "volume_to_marketcap": volume_to_marketcap,
        # metadata
        "source": "coingecko",
        "raw_file": str(source_file) if source_file else None,
        "ingestion_timestamp_utc": ingestion_ts,
        "run_id": run_id or getattr(settings, "RUN_ID", None),
    }

    return out


def run_transform(coins: list[str], run_id: Optional[str] = None) -> pd.DataFrame:
    """
    Run transform for multiple coins and return a DataFrame.
    Invalid raw records are written to the dead-letter and skipped.
    """
    logger.info("Starting data transformation")

    rows = []

    for coin in coins:
        try:
            raw_data, raw_path = load_latest_coingecko_file(coin)
        except FileNotFoundError:
            logger.warning("No raw file for %s; skipping", coin)
            continue

        try:
            transformed = transform_market_data(raw_data, source_file=raw_path, run_id=run_id)
            rows.append(transformed)
        except InvalidRawDataError as e:
            logger.warning("Invalid raw data for %s: %s; sent to dead-letter", coin, e)
            continue
        except KeyError as e:
            logger.warning("Missing expected field for %s: %s; skipping", coin, e)
            _write_dead_letter(source=coin, payload=raw_data, error=f"KeyError: {e}", meta={"source_file": str(raw_path)}, stage="transform", run_id=run_id)
            continue
        except Exception:
            logger.exception("Unexpected error transforming %s; sending to dead-letter", coin)
            _write_dead_letter(source=coin, payload=raw_data, error="Unexpected transform error", meta={"source_file": str(raw_path)}, stage="transform", run_id=run_id)
            continue

    df = pd.DataFrame(rows)
    logger.info("Transformation complete: %d rows", len(df))
    return df


def save_processed_data(df: pd.DataFrame):
    """
    Save processed market data to CSV.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = PROCESSED_DATA_DIR / f"market_data_{timestamp}.csv"

    df.to_csv(file_path, index=False)
    logger.info("Processed market data saved to %s", file_path)