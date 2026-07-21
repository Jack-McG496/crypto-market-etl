from src.transform.market_data_transform import run_transform
from src.load.postgres_loader import load_market_data
import pandas as pd
import pytest

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
