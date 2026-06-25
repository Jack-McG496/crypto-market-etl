from src.analytics.data_loader import load_price_history
from src.analytics.volatility_analysis import calculate_volatility_features
from src.analytics.anomaly_detection import detect_anomalies
from src.analytics.regime_detection import classify_volatility_regime
from src.load.analytics_loader import load_analytics_data
from src.utils.logger import get_logger

logger = get_logger(__name__)

def run_analytics_pipeline(sentiment_score, sentiment_label):
    price_df = load_price_history(days=90)

    analytics_df = calculate_volatility_features(price_df)

    logger.info(f"Rows entering anomaly detection: {len(analytics_df)}")

    analytics_anomaly_df = detect_anomalies(
        analytics_df,
        sentiment_score,
        sentiment_label
    )

    analytics_anomaly_df = classify_volatility_regime(analytics_anomaly_df)

    logger.info(f"Analytics rows produced: {len(analytics_anomaly_df)}")
    logger.info(f"Analytics columns: {analytics_anomaly_df.columns.tolist()}")

    # Load analytics
    load_analytics_data(analytics_anomaly_df)

    return analytics_anomaly_df