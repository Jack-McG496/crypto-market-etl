import pandas as pd
import pytest

@pytest.fixture
def sample_market_df():

    return pd.DataFrame({
        "coin_id": ["btc"] * 20,
        "timestamp_utc": pd.date_range("2026-01-01", periods=20, freq="h"),
        "price_usd": [100, 110, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111]
    })

@pytest.fixture
def sample_history_df():

    return pd.DataFrame({
        "coin_id": ["btc"] * 60,
        "timestamp_utc": pd.date_range("2026-01-01", periods=60, freq="h"),
        "price_usd": [100, 110, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111,
                      100, 130, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111,
                      100, 140, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111]
    })