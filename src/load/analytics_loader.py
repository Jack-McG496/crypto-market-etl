import psycopg2
from psycopg2.extras import execute_batch
import logging
import os

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "crypto_db"),
        user=os.getenv("POSTGRES_USER", "crypto"),
        password=os.getenv("POSTGRES_PASSWORD", "crypto")
    )


def load_analytics_data(df):
    if df.empty:
        logging.warning("No analytics data to load")
        return

    insert_sql = """
    INSERT INTO volatility_alerts (
        coin_id,
        z_score,
        threshold,
        sentiment_score,
        sentiment_label,
        is_anomalous,
        timestamp_utc
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (coin_id, timestamp_utc)
    DO UPDATE SET
        z_score = EXCLUDED.z_score,
        threshold = EXCLUDED.threshold,
        sentiment_score = EXCLUDED.sentiment_score,
        sentiment_label = EXCLUDED.sentiment_label,
        is_anomalous = EXCLUDED.is_anomalous;
    """

    records = [
        (
            row["coin_id"],
            row["z_score"],
            row["threshold"],
            row["sentiment_score"],
            row["sentiment_label"],
            row["is_anomalous"],
            row["timestamp_utc"]
        )
        for _, row in df.iterrows()
    ]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_batch(cur, insert_sql, records, page_size=100)
        conn.commit()
        logging.info(f"Loaded {len(records)} rows into analytics table")
    except Exception:
        conn.rollback()
        logging.exception("Failed to load analytics data")
        raise
    finally:
        conn.close()
