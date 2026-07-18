from psycopg2.extras import execute_batch
from src.utils.logger import get_logger
from src.utils.db import get_connection
import pandas as pd

logger = get_logger(__name__)


def ensure_alerts_table_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'alerts'
                  AND column_name = 'notified'
            )
        """)
        exists = cur.fetchone()[0]

        if not exists:
            cur.execute("""
                ALTER TABLE alerts
                ADD COLUMN notified BOOLEAN DEFAULT FALSE;
            """)
            conn.commit()
            logger.info("Added missing notified column to alerts table")

    return conn


def load_alert_data(df):
    if df.empty:
        logger.warning("No alert data to load")
        return

    conn = get_connection()
    try:
        ensure_alerts_table_schema(conn)

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
        ensure_alerts_table_schema(conn)
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