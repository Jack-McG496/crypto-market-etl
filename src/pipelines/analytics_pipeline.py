import time

from src.analytics.anomaly_detection import detect_anomalies
from src.analytics.data_loader import load_price_history
from src.analytics.regime_detection import classify_volatility_regime
from src.analytics.volatility_analysis import calculate_volatility_features
from src.load.analytics_loader import load_analytics_data
from src.pipelines.metrics import PipelineMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_analytics_pipeline(sentiment_score: int, sentiment_label: str, metrics=None, run_id: str | None = None):
    if metrics is None:
        metrics = PipelineMetrics(run_id=run_id)
    start = time.perf_counter()
    logger = get_logger(__name__, run_id=run_id, stage="analytics", task="analytics_pipeline")

    logger.info("Starting analytics pipeline")

    price_df = load_price_history()

    analytics_df = calculate_volatility_features(price_df)

    logger.info(f"Rows entering anomaly detection: {len(analytics_df)}")
    metrics.analytics_rows = len(analytics_df)

    analytics_anomaly_df = detect_anomalies(
        analytics_df,
        sentiment_score,
        sentiment_label
    )

    analytics_anomaly_df = classify_volatility_regime(analytics_anomaly_df)

    logger.info(f"Analytics rows produced: {len(analytics_anomaly_df)}")
    logger.info(f"Analytics columns: {analytics_anomaly_df.columns.tolist()}")

    load_analytics_data(analytics_anomaly_df, run_id=run_id)

    logger.info("Analytics completed in %.2fs", time.perf_counter() - start)

    return analytics_anomaly_df
