import pandas as pd
from src.analytics.volatility_analysis import calculate_volatility_features

def test_returns_are_computed():

    # Mock data
    df = pd.DataFrame({
        "coin_id": ["btc"] * 5,
        "timestamp_utc": pd.date_range("2025-01-01", periods=5, freq="h"),
        "price_usd": [100, 110, 120, 118, 130]
    })

    # Call function
    result = calculate_volatility_features(
        df,
        window=3
    )

    # Assert result
    assert "returns" in result.columns