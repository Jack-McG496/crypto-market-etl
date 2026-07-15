from src.transform.market_data_transform import run_transform
from src.load.postgres_loader import load_market_data
from src.utils.db import get_connection
import pandas as pd

def test_market_pipeline():
    market_df = run_transform(["bitcoin"])

    load_market_data(market_df)

    conn = get_connection()

    count = pd.read_sql("SELECT COUNT(*) FROM market_data", conn)

    coin_id = pd.read_sql("SELECT coin_id FROM market_data LIMIT 1", conn)
    price = pd.read_sql("SELECT price_usd FROM market_data LIMIT 1", conn)
    market_cap = pd.read_sql("SELECT market_cap FROM market_data LIMIT 1", conn)

    assert count == len(market_df)

    assert coin_id == "bitcoin"
    assert price == "80445"
    assert market_cap == "1805359545455"
