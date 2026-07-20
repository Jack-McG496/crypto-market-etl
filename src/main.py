from src.pipelines.extraction_pipeline import run_extraction_pipeline
from src.pipelines.market_pipeline import run_market_pipeline
from src.pipelines.analytics_pipeline import run_analytics_pipeline
from src.pipelines.alert_pipeline import run_alert_pipeline
from src.pipelines.metrics import PipelineMetrics
from src.pipelines.notification_pipeline import run_notification_pipeline
from src.utils.logger import get_logger
from dotenv import load_dotenv

import time

load_dotenv()

logger = get_logger(__name__)
metrics = PipelineMetrics()

def main():
    start = time.perf_counter()
    logger.info("Pipeline started")

    try:
        # Extract
        run_extraction_pipeline()

        # Transform
        _, sentiment_df = run_market_pipeline()

        # Analytics
        sentiment_score = sentiment_df["sentiment_score"].iloc[-1]
        sentiment_label = sentiment_df["sentiment_label"].iloc[-1]
        analytics_df = run_analytics_pipeline(sentiment_score, sentiment_label)

        # Alerts
        run_alert_pipeline(analytics_df)

        # Notifications

        run_notification_pipeline()

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
