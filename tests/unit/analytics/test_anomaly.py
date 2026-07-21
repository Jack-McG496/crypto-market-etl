from src.analytics.anomaly_detection import detect_anomalies
import pandas as pd

def test_anomaly_above_detection():
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
    assert result.iloc[0]["is_anomalous"]

def test_anomaly_below_detection():
    # Mock data
    df = pd.DataFrame({
        "coin_id": ["btc"],
        "timestamp_utc": pd.date_range("2026-01-01", periods=1, freq="h"),
        "price_usd": [100],
        "z_score": [0]
    })

    # Call function
    result = detect_anomalies(df, 50, "SENTIMENT_LABEL")

    # Assert result
    assert not result.iloc[0]["is_anomalous"]

def test_anomaly_extreme_greed():
    # Mock data
    df = pd.DataFrame({
        "coin_id": ["btc"],
        "timestamp_utc": pd.date_range("2026-01-01", periods=1, freq="h"),
        "price_usd": [100],
        "z_score": [0]
    })

    # Call function
    result = detect_anomalies(df, 80, "GREED")

    # Assert result
    assert result.iloc[0]["threshold"] == 2.5

def test_anomaly_extreme_fear():
    # Mock data
    df = pd.DataFrame({
        "coin_id": ["btc"],
        "timestamp_utc": pd.date_range("2026-01-01", periods=1, freq="h"),
        "price_usd": [100],
        "z_score": [0]
    })

    # Call function
    result = detect_anomalies(df, 20, "FEAR")

    # Assert result
    assert result.iloc[0]["threshold"] == 2.0