import time

from src.config.settings import settings
from src.pipelines.alert_pipeline import run_alert_pipeline
from src.pipelines.analytics_pipeline import run_analytics_pipeline
from src.pipelines.extraction_pipeline import run_extraction_pipeline
from src.pipelines.market_pipeline import run_market_pipeline
from src.pipelines.metrics import PipelineMetrics
from src.pipelines.metrics_writer import persist_run_metrics
from src.pipelines.notification_pipeline import run_notification_pipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main(run_id: str | None = None):
    metrics = PipelineMetrics(run_id=run_id or getattr(settings, "RUN_ID", None))
    start = time.perf_counter()
    logger = get_logger(__name__, run_id=metrics.run_id, stage="pipeline", task="main")
    logger.info("Pipeline started")

    try:
        run_extraction_pipeline(run_id=metrics.run_id)

        _, sentiment_df = run_market_pipeline(metrics, run_id=metrics.run_id)

        sentiment_score = sentiment_df["sentiment_score"].iloc[-1]
        sentiment_label = sentiment_df["sentiment_label"].iloc[-1]
        analytics_df = run_analytics_pipeline(sentiment_score, sentiment_label, metrics, run_id=metrics.run_id)

        run_alert_pipeline(analytics_df, metrics, run_id=metrics.run_id)
        run_notification_pipeline(metrics, run_id=metrics.run_id)

        logger.info("Pipeline finished successfully")
        metrics.status = "success"
    except Exception:
        metrics.status = "failed"
        logger.exception("ETL pipeline failed")
        raise
    finally:
        metrics.run_duration = time.perf_counter() - start
        metrics.duration_seconds = metrics.run_duration
        metrics.rows_ingested = max(metrics.market_rows, metrics.rows_ingested)
        logger.info("Pipeline Metrics | %s", metrics)
        logger.info("ETL pipeline completed in %.2f seconds", metrics.run_duration)
        persist_run_metrics(metrics)


if __name__ == "__main__":
    main()
