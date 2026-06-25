import pandas as pd
from src.load.postgres_loader import get_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_price_history(days=90):
    """
    Load historical price data from market_data table.
    Used for volatility calculations.
    """

    logger.info("Loading price history from database")

    conn = get_connection()

    query = """
        SELECT
            coin_id,
            timestamp_utc,
            price_usd
        FROM market_data
        ORDER BY coin_id, timestamp_utc
    """

    df = pd.read_sql(query, conn)
    conn.close()

    logger.info(f"Loaded price history rows: {len(df)}")

    if not df.empty:
        logger.info("Rows per coin:")
        logger.info(df.groupby("coin_id").size())

    return df
