from src.analytics.volatility_analysis import calculate_volatility_features
from src.analytics.anomaly_detection import detect_anomalies
from src.analytics.regime_detection import classify_volatility_regime
from src.alerts.alert_engine import generate_alerts
from tests.conftest import sample_history_df
import pytest

@pytest.mark.integration
def test_analytics_pipeline():

    price_df = sample_history_df()

    analytics = calculate_volatility_features(price_df)

    analytics = detect_anomalies(
        analytics,
        80,
        "Greed"
    )

    analytics = classify_volatility_regime(
        analytics
    )

    alerts = generate_alerts(analytics)

    assert len(analytics) > 0

    assert "z_score" in analytics.columns

    assert "volatility_regime" in analytics.columns

    assert "is_anomalous" in analytics.columns

    assert "VOLATILITY" in alerts['alert_type'].values

    assert "SENTIMENT" in alerts['alert_type'].values

    assert "REGIME_CHANGE" in alerts['alert_type'].values
