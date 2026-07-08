import pandas as pd
from src.analytics.volatility_analysis import calculate_volatility_features

def test_returns_are_computed():

    # Mock data
    df = pd.DataFrame({
        "coin_id": ["btc"] * 20,
        "timestamp_utc": pd.date_range("2026-01-01", periods=20, freq="h"),
        "price_usd": [100, 110, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111]
    })

    # Call function
    result = calculate_volatility_features(
        df,
        window=10
    )

    # Assert result
    assert "returns" in result.columns

def test_rolling_std_computed():

    df = pd.DataFrame({
        "coin_id": ["btc"] * 20,
        "timestamp_utc": pd.date_range("2026-01-01", periods=20, freq="h"),
        "price_usd": [100, 110, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111]
    })

    result = calculate_volatility_features(
        df,
        window=10
    )

    assert "rolling_std" in result.columns

def test_z_score_computed():

    df = pd.DataFrame({
        "coin_id": ["btc"] * 20,
        "timestamp_utc": pd.date_range("2026-01-01", periods=20, freq="h"),
        "price_usd": [100, 110, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111]
    })

    result = calculate_volatility_features(
        df,
        window=10
    )

    assert "z_score" in result.columns