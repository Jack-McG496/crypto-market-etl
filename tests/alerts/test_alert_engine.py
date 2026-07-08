import pandas as pd
from src.alerts.alert_engine import generate_alerts

def test_alert_generation():
    df = pd.DataFrame({
        "coin_id": "btc",
        "timestamp_utc": pd.date_range("2026-01-01", periods=1, freq="h"),
        "is_anomalous": [True]
    })

    result = generate_alerts(df)

    assert len(result)==1