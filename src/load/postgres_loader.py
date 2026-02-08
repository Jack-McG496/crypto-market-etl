from psycopg2.extras import execute_batch
import logging
from src.utils.db import get_connection

def load_market_data(df):
    if df.empty:
        logging.warning("No data to load")
        return

    insert_sql = """
    INSERT INTO market_data (
        coin_id,
        price_usd,
        volume_24h,
        market_cap,
        timestamp_utc
    )
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (coin_id, timestamp_utc)
    DO UPDATE SET
        price_usd = EXCLUDED.price_usd,
        volume_24h = EXCLUDED.volume_24h,
        market_cap = EXCLUDED.market_cap;
    """

    records = [
        (
            row["coin_id"],
            row["price_usd"],
            row["total_volume_usd"],
            row["market_cap_usd"],
            row["timestamp_utc"]
        )
        for _, row in df.iterrows()
    ]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_batch(cur, insert_sql, records, page_size=100)
        conn.commit()
        logging.info(f"Loaded {len(records)} rows into Postgres")
    except Exception:
        conn.rollback()
        logging.exception("Failed to load market data")
        raise
    finally:
        conn.close()
