from src.pipelines.extraction_pipeline import run_extraction_pipeline
from src.pipelines.market_pipeline import run_market_pipeline
from src.pipelines.analytics_pipeline import run_analytics_pipeline
from src.pipelines.alert_pipeline import run_alert_pipeline
from src.pipelines.metrics import PipelineMetrics
from src.pipelines.notification_pipeline import run_notification_pipeline
from src.utils.logger import get_logger

import time

logger = get_logger(__name__)

def main():
    metrics = PipelineMetrics()

    start = time.perf_counter()
    logger.info("Pipeline started")

    try:
        # Extract
        run_extraction_pipeline()

        # Transform
        _, sentiment_df = run_market_pipeline(metrics)

        # Analytics
        sentiment_score = sentiment_df["sentiment_score"].iloc[-1]
        sentiment_label = sentiment_df["sentiment_label"].iloc[-1]
        analytics_df = run_analytics_pipeline(sentiment_score, sentiment_label, metrics)

        # Alerts
        run_alert_pipeline(analytics_df, metrics)

        # Notifications

        run_notification_pipeline(metrics)

        logger.info("Pipeline finished successfully")

    except Exception:
        logger.exception("ETL pipeline failed")
        raise

    finally:
        elapsed = time.perf_counter() - start
        logger.info("Pipeline Metrics | %s", metrics)
        logger.info("ETL pipeline completed in %.2f seconds", elapsed)

if __name__ == "__main__":
    main()
