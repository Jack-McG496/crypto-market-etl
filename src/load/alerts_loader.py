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


def validate_alert_record(row):
    required = ["coin_id", "alert_type", "severity", "message"]
    missing = [key for key in required if row.get(key) is None or str(row.get(key)).strip() == ""]
    if missing:
        raise ValueError(f"Missing required alert fields: {missing}")
    return True


def normalize_alert_record(row):
    validate_alert_record(row)
    created_at = row.get("created_at") or pd.Timestamp.utcnow()
    analytics_timestamp = row.get("analytics_timestamp") or created_at
    return (
        row["coin_id"],
        row["alert_type"],
        row["severity"],
        row["message"],
        created_at,
        analytics_timestamp,
        bool(row.get("notified", False)),
    )


def load_alert_data(df: pd.DataFrame, run_id: str | None = None):
    """
    Loads alert data into alert table.
    """
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
            analytics_timestamp,
            notified
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (coin_id, created_at)
        DO UPDATE SET
            alert_type = EXCLUDED.alert_type,
            severity = EXCLUDED.severity,
            message = EXCLUDED.message,
            analytics_timestamp = EXCLUDED.analytics_timestamp,
            notified = alerts.notified OR EXCLUDED.notified;
        """

        records = []
        for _, row in df.iterrows():
            try:
                records.append(normalize_alert_record(row))
            except ValueError as exc:
                logger.warning("Skipping invalid alert row: %s | error=%s", row.to_dict(), exc)

        if not records:
            logger.warning("No valid alert rows to load after validation")
            return

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


def load_pending_alerts() -> pd.DataFrame:
    """
    Returns a panda dataframe of alerts from database that have yet to be processed.
    """

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


def mark_alert_notified(conn, alert_id: str):
    query = """
    UPDATE alerts
    SET notified = TRUE
    WHERE id = %s AND notified IS DISTINCT FROM TRUE;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(query, (alert_id,))
    except Exception:
        conn.rollback()
        logger.exception("Failed to update alert data")
        raise