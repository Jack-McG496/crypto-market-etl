from unittest.mock import patch
import pandas as pd
from src.alerts.alert_engine import generate_alerts
from src.load.alerts_loader import load_alert_data
from src.pipelines.notification_pipeline import run_notification_pipeline

@patch("requests.post")
def test_notification(mock_post):
    mock_post.return_value.status_code = 200

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

    run_notification_pipeline()

    args, kwargs = mock_post.call_args

    assert mock_post.assert_called_once()

    assert kwargs["json"]["text"] == \
           "btc volatility exceeded threshold"


