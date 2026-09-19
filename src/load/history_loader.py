from datetime import datetime

from psycopg2.extras import execute_batch

from src.utils.db import get_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)


def normalize_historical_record(row):
    return (
        row["coin_id"],
        row.get("timestamp_utc"),
        row["price_usd"],
        row.get("volume_24h"),
        row.get("ingested_at") or row.get("ingestion_timestamp_utc") or datetime.utcnow(),
        row.get("source_file") or row.get("raw_file"),
        row.get("run_id"),
    )


def load_historical_data(records: list, run_id: str | None = None):

    if not records:
        logger.warning("No historical data to load")
        return

    insert_sql = """
    INSERT INTO market_data (
        coin_id,
        timestamp_utc,
        price_usd,
        volume_24h,
        ingested_at,
        source_file,
        run_id
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (coin_id, timestamp_utc)
    DO UPDATE SET
        price_usd = EXCLUDED.price_usd,
        volume_24h = EXCLUDED.volume_24h,
        ingested_at = EXCLUDED.ingested_at,
        source_file = EXCLUDED.source_file,
        run_id = EXCLUDED.run_id;
    """

    values = [normalize_historical_record(r) for r in records]

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            execute_batch(cur, insert_sql, values, page_size=500)

        conn.commit()

        logger.info(f"Loaded {len(values)} historical rows")

    except Exception:
        conn.rollback()
        logger.exception("History load failed")
        raise

    finally:
        conn.close()
