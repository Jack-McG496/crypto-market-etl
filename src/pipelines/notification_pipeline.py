import time

from src.load.alerts_loader import load_pending_alerts, mark_alert_notified
from src.notifications.slack_notifier import send_slack_alert
from src.pipelines.metrics import PipelineMetrics
from src.utils.db import get_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_notification_pipeline(metrics=None, run_id: str | None = None):
    if metrics is None:
        metrics = PipelineMetrics(run_id=run_id)
    start = time.perf_counter()
    logger = get_logger(__name__, run_id=run_id, stage="notifications", task="notification_pipeline")
    logger.info("Starting notification pipeline")

    sent = 0
    failed = 0

    pending_alerts = load_pending_alerts()

    logger.info(f"Number of pending alerts: {len(pending_alerts)}")

    if pending_alerts.empty:
        return

    conn = get_connection()

    try:
        for _, alert in pending_alerts.iterrows():
            try:
                success = send_slack_alert(alert)
                if success:
                    with conn:
                        mark_alert_notified(conn, alert["id"])
                    sent += 1
                else:
                    failed += 1
                    logger.warning("Notification failed for alert %s", alert.get("id"))
            except Exception:
                failed += 1
                conn.rollback()
                logger.exception("Failed to notify alert %s", alert.get("id"))
    finally:
        conn.close()

    logger.info("Notifications complete | sent=%d failed=%d", sent, failed)
    metrics.notifications_sent = sent
    metrics.notifications_failed = failed
    logger.info("Notifications completed in %.2fs", time.perf_counter() - start)
    logger.info("Notification pipeline complete")
