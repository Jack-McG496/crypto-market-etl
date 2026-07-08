import pandas as pd
from src.analytics.anomaly_detection import detect_anomalies

def test_anomaly_detection():
    # Mock data
    df = pd.DataFrame({
        "coin_id": ["btc"],
        "timestamp_utc": pd.date_range("2026-01-01", periods=1, freq="h"),
        "price_usd": [100],
        "z_score": [10]
    })

    # Call function
    result = detect_anomalies(df, 50, "SENTIMENT_LABEL")

    # Assert result
    assert result.iloc[0]["is_anomalous"] == True