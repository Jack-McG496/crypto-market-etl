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

@pytest.fixture
def sample_raw_json_coingecko():

    return {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "market_data": {
            "current_price": {
                "usd": 80445
            },
            "market_cap": {
                "usd": 1805359545455
            },
            "total_volume": {
                "usd": 35347384019
            },
            "circulating_supply": 19974862.0,
            "price_change_percentage_24h": {
                "usd": -0.16067
            }
        }
    }