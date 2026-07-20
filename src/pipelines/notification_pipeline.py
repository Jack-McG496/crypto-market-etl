from src.notifications.slack_notifier import send_slack_alert
from src.load.alerts_loader import load_pending_alerts
from src.load.alerts_loader import mark_alert_notified
from src.utils.db import get_connection
from src.utils.logger import get_logger
from src.main import metrics
import time
logger = get_logger(__name__)

def run_notification_pipeline():
    start = time.perf_counter()
    logger.info("Starting notification pipeline")

    sent = 0
    failed = 0

    pending_alerts = load_pending_alerts()

    logger.info(f"Number of pending alerts: {len(pending_alerts)}")

    if pending_alerts.empty:
        return

    conn = get_connection()

    for _, alert in pending_alerts.iterrows():

        success = send_slack_alert(alert)

        if success:
            sent += 1
            mark_alert_notified(conn, alert["id"])
        else:
            failed += 1

    logger.info("Notifications complete | sent=%d failed=%d", sent, failed)
    metrics.notifications_sent = sent
    metrics.notifications_failed = failed
    logger.info("Notifications completed in %.2fs", time.perf_counter() - start)
    logger.info("Notification pipeline complete")
