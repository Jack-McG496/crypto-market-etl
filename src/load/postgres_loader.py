import json
from datetime import datetime

from psycopg2.extras import Json, execute_batch
from src.utils.logger import get_logger
from src.utils.db import get_connection
import pandas as pd

logger = get_logger(__name__)


def validate_market_record(row):
    required = ["coin_id", "price_usd", "timestamp_utc"]
    missing = [key for key in required if row.get(key) is None]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    for key in ("price_usd", "market_cap_usd", "total_volume_usd", "market_cap", "volume_24h"):
        value = row.get(key)
        if value is not None:
            try:
                float(value)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid numeric value for {key}: {value!r}")

    return True


def normalize_market_record(row):
    """Normalize a market row to the schema expected by the Postgres loader."""
    validate_market_record(row)

    timestamp_utc = row.get("timestamp_utc")
    ingested_at = row.get("ingested_at") or row.get("ingestion_timestamp_utc") or datetime.utcnow()
    source_file = row.get("source_file") if row.get("source_file") is not None else row.get("raw_file")
    volume_24h = row.get("total_volume_usd") if row.get("total_volume_usd") is not None else row.get("volume_24h")
    market_cap = row.get("market_cap_usd") if row.get("market_cap_usd") is not None else row.get("market_cap")
    run_id = row.get("run_id")

    return (
        row["coin_id"],
        row["price_usd"],
        volume_24h,
        market_cap,
        timestamp_utc,
        ingested_at,
        source_file,
        run_id,
    )


def write_dead_letter_event(source: str, stage: str, payload, error: str, run_id=None):
    try:
        conn = get_connection()
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
    except Exception:
        logger.exception("Failed to write dead-letter event for failed market-data batch")


def load_market_data(df: pd.DataFrame, run_id: str | None = None):
    """
    Loads market data to market_data table.
    """
    if df.empty:
        logger.warning("No data to load")
        return

    insert_sql = """
    INSERT INTO market_data (
        coin_id,
        price_usd,
        volume_24h,
        market_cap,
        timestamp_utc,
        ingested_at,
        source_file,
        run_id
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (coin_id, timestamp_utc)
    DO UPDATE SET
        price_usd = EXCLUDED.price_usd,
        volume_24h = EXCLUDED.volume_24h,
        market_cap = EXCLUDED.market_cap,
        ingested_at = EXCLUDED.ingested_at,
        source_file = EXCLUDED.source_file,
        run_id = EXCLUDED.run_id;
    """

    records = []
    for _, row in df.iterrows():
        try:
            records.append(normalize_market_record(row))
        except ValueError as exc:
            logger.warning("Skipping invalid market row: %s | error=%s", row.to_dict(), exc)
            write_dead_letter_event(
                source="market_data_loader",
                stage="load_market_data",
                payload=row.to_dict(),
                error=str(exc),
                run_id=row.get("run_id"),
            )

    if not records:
        logger.warning("No valid market rows to load after validation")
        return

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_batch(cur, insert_sql, records, page_size=100)
        conn.commit()
        logger.info(f"Loaded {len(records)} rows into market data Postgres")
    except Exception as exc:
        conn.rollback()
        logger.exception("Failed to load market data")
        write_dead_letter_event(
            source="market_data_loader",
            stage="load_market_data",
            payload={"records": [list(record) for record in records]},
            error=str(exc),
            run_id=None,
        )
        raise
    finally:
        conn.close()
