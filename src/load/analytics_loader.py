from psycopg2.extras import execute_batch
from src.utils.logger import get_logger
from src.utils.db import get_connection
import pandas as pd

logger = get_logger(__name__)

def load_analytics_data(df: pd.DataFrame):
    """
    Loads transformed analytics into volatility_alerts table.
    """
    if df.empty:
        logger.warning("No analytics data to load")
        return

    insert_sql = """
    INSERT INTO volatility_alerts (
        coin_id,
        returns,
        rolling_std,
        z_score,
        threshold,
        sentiment_score,
        sentiment_label,
        is_anomalous,
        volatility_regime,
        timestamp_utc
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (coin_id, timestamp_utc)
    DO UPDATE SET
    returns = EXCLUDED.returns,
    rolling_std = EXCLUDED.rolling_std,
    z_score = EXCLUDED.z_score,
    threshold = EXCLUDED.threshold,
    sentiment_score = EXCLUDED.sentiment_score,
    sentiment_label = EXCLUDED.sentiment_label,
    is_anomalous = EXCLUDED.is_anomalous,
    volatility_regime = EXCLUDED.volatility_regime;
    """

    records = [
        (
            row["coin_id"],
            row["returns"],
            row["rolling_std"],
            row["z_score"],
            row["threshold"],
            row["sentiment_score"],
            row["sentiment_label"],
            row["is_anomalous"],
            row["volatility_regime"],
            row["timestamp_utc"]
        )
        for _, row in df.iterrows()
    ]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_batch(cur, insert_sql, records, page_size=100)
        conn.commit()
        logger.info(f"Loaded {len(records)} rows into analytics table")
    except Exception:
        conn.rollback()
        logger.exception("Failed to load analytics data")
        raise
    finally:
        conn.close()
