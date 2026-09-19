import time

from src.alerts.alert_engine import generate_alerts
from src.load.alerts_loader import load_alert_data
from src.pipelines.metrics import PipelineMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_alert_pipeline(analytics_df, metrics=None, run_id: str | None = None):
    if metrics is None:
        metrics = PipelineMetrics(run_id=run_id)
    start = time.perf_counter()
    logger = get_logger(__name__, run_id=run_id, stage="alerts", task="alert_pipeline")
    logger.info("Starting alerts pipeline")

    alerts_df = generate_alerts(analytics_df, metrics)
    load_alert_data(alerts_df, run_id=run_id)

    logger.info("Alerts generated in %.2fs", time.perf_counter() - start)
    logger.info("Alert pipeline complete")

    return alerts_df
