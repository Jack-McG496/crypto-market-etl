import pandas as pd
from src.utils.db import get_connection


def load_price_history(days=90):

    query = """
    SELECT
        coin_id,
        timestamp_utc,
        price_usd
    FROM market_data
    WHERE timestamp_utc >= NOW() - INTERVAL '%s days'
    ORDER BY coin_id, timestamp_utc;
    """

    conn = get_connection()

    df = pd.read_sql(query, conn, params=(days,))

    conn.close()

    return df
