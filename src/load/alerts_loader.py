from psycopg2.extras import execute_batch
import logging
from src.utils.db import get_connection

def load_alert_data(df):
    if df.empty:
        logging.warning("No alert data to load")
        return

    insert_sql = """
    INSERT INTO alerts (
        coin_id,
        alert_type,
        severity,
        message,
        created_at,
        analytics_timestamp
    )
    VALUES (%s,%s,%s,%s,%s,%s)
    ON CONFLICT (coin_id, created_at)
    DO NOTHING;
    """

    records = [
        (
            row["coin_id"],
            row["alert_type"],
            row["severity"],
            row["message"],
            row["z_score"],
            row["created_at"],
            row["analytics_timestamp"]
        )
        for _, row in df.iterrows()
    ]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_batch(cur, insert_sql, records, page_size=100)
        conn.commit()
        logging.info(f"Loaded {len(records)} rows into alerts table")
    except Exception:
        conn.rollback()
        logging.exception("Failed to load alert data")
        raise
    finally:
        conn.close()
