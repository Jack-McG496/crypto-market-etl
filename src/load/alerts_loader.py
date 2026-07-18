from psycopg2.extras import execute_batch
from src.utils.logger import get_logger
from src.utils.db import get_connection
import pandas as pd

logger = get_logger(__name__)

def load_alert_data(df):
    if df.empty:
        logger.warning("No alert data to load")
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
        logger.info(f"Loaded {len(records)} rows into alerts table")
    except Exception:
        conn.rollback()
        logger.exception("Failed to load alert data")
        raise
    finally:
        conn.close()

def load_pending_alerts():

    sql = """
    SELECT *
    FROM alerts
    WHERE notified = FALSE
    ORDER BY created_at;
    """

    conn = get_connection()

    try:
        return pd.read_sql(sql, conn)

    finally:
        conn.close()


def mark_alert_notified(conn, alert_id):
    query = """
    UPDATE alerts SET notified = TRUE WHERE id = %s; 
    """

    try:
        with conn.cursor() as cur:
            cur.execute(query, (alert_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to update alert data")
        raise
    finally:
        conn.close()
