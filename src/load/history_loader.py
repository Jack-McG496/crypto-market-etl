import psycopg2
from psycopg2.extras import execute_batch
from src.utils.db import get_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_historical_data(records):

    if not records:
        logger.warning("No historical data to load")
        return

    insert_sql = """
    INSERT INTO market_data (
        coin_id,
        timestamp_utc,
        price_usd,
        volume_24h
    )
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (coin_id, timestamp_utc)
    DO NOTHING;
    """

    values = [
        (
            r["coin_id"],
            r["timestamp_utc"],
            r["price_usd"],
            r["volume_24h"]
        )
        for r in records
    ]

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
