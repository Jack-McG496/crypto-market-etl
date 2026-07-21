import pytest as pytest

from src.alerts.alert_engine import generate_alerts
from src.load.alerts_loader import load_alert_data
import pandas as pd

@pytest.mark.integration
def test_alert_pipeline(db_connection):
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

    conn = db_connection

    count_df = pd.read_sql("SELECT COUNT(*) FROM alerts", conn)

    alert_df = pd.read_sql("SELECT * FROM alerts", conn)

    assert count_df.iloc[0, 0] == 1

    assert alert_df.iloc[0]["alert_type"] == "VOLATILITY"
    assert alert_df.iloc[0]["severity"] == "WARNING"
    assert "bitcoin" in alert_df.iloc[0]["message"]

