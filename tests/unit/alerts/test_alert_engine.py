import pandas as pd
from src.alerts.alert_engine import generate_alerts

def test_volatility_alert_generation():
    df = pd.DataFrame({
        "coin_id": "btc",
        "timestamp_utc": pd.date_range("2026-01-01", periods=1, freq="h"),
        "is_anomalous": [True]
    })

    result = generate_alerts(df)

    assert result.iloc[0]["alert_type"] == "VOLATILITY"

def test_regime_change_alert_generation():
    df = pd.DataFrame({
        "coin_id": ["btc"] * 2,
        "timestamp_utc": pd.date_range("2026-01-01", periods=2, freq="h"),
        "volatility_regime": ["High", "Extreme"]
    })

    result = generate_alerts(df)

    assert result.iloc[0]["alert_type"] == "REGIME_CHANGE"

def test_sentiment_alert_generation():
    df = pd.DataFrame({
        "coin_id": "btc",
        "timestamp_utc": pd.date_range("2026-01-01", periods=1, freq="h"),
        "sentiment_score": [80]
    })

    result = generate_alerts(df)

    assert result.iloc[0]["alert_type"] == "SENTIMENT"

def test_regime_severity_alert():
    df = pd.DataFrame({
        "coin_id": ["btc"] * 2,
        "timestamp_utc": pd.date_range("2026-01-01", periods=2, freq="h"),
        "volatility_regime": ["High", "Extreme"]
    })

    result = generate_alerts(df)

    assert result.iloc[0]["severity"] == "CRITICAL"