import pandas as pd
from src.alerts.alert_engine import generate_alerts
from src.load.alerts_loader import load_alert_data
from src.utils.db import get_connection

def test_alert_pipeline():
    df = pd.DataFrame({
        "coin_id": "btc",
        "timestamp_utc": pd.date_range("2026-01-01", periods=1, freq="h"),
        "is_anomalous": [True],
        "volatility_regime": ["Extreme"],
        "sentiment_score": [50],
        "threshold": [3],
        "z_score": [3.8]
    })

    alerts = generate_alerts(df)

    load_alert_data(alerts)

    conn = get_connection()

    count = pd.read_sql("SELECT COUNT(*) FROM alerts", conn)

    alert_df = pd.read_sql("SELECT * FROM alerts", conn)

    assert count == 1

    assert alert_df["alert_type"] == "VOLATILITY"
    assert alert_df["severity"] == "WARNING"
    assert "bitcoin" in alert_df["message"]

