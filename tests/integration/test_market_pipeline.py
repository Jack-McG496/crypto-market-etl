import pandas as pd
import pytest

from src.load.postgres_loader import load_market_data
from src.transform.market_data_transform import run_transform


@pytest.mark.integration
def test_market_pipeline(db_connection):
    market_df = run_transform(["bitcoin"])

    load_market_data(market_df)

    conn = db_connection

    count = pd.read_sql("SELECT COUNT(*) FROM market_data", conn)

    coin_id = pd.read_sql("SELECT coin_id FROM market_data LIMIT 1", conn)
    price = pd.read_sql("SELECT price_usd FROM market_data LIMIT 1", conn)
    market_cap = pd.read_sql("SELECT market_cap FROM market_data LIMIT 1", conn)

    assert count.iloc[0, 0] == len(market_df)

    assert coin_id.iloc[0, 0] == "bitcoin"
    assert price.iloc[0, 0] == "80445"
    assert market_cap.iloc[0, 0] == "1805359545455"


@pytest.mark.integration
def test_market_loader_is_idempotent_for_duplicate_batch(db_connection):
    conn = db_connection
    unique_coin = "btc_idempotent"
    conn.cursor().execute("DELETE FROM market_data WHERE coin_id = %s", (unique_coin,))
    conn.commit()

    df = pd.DataFrame(
        {
            "coin_id": [unique_coin] * 5,
            "price_usd": [100.0, 101.0, 102.0, 103.0, 104.0],
            "timestamp_utc": pd.date_range("2026-02-01 00:00:00", periods=5, freq="h"),
            "market_cap": [1000.0] * 5,
            "volume_24h": [50.0] * 5,
            "run_id": ["repeat-load-1"] * 5,
        }
    )

    load_market_data(df, run_id="repeat-load-1")
    load_market_data(df, run_id="repeat-load-2")

    count = pd.read_sql(
        "SELECT COUNT(*) FROM market_data WHERE coin_id = %s",
        conn,
        params=(unique_coin,),
    ).iloc[0, 0]

    assert count == len(df)
