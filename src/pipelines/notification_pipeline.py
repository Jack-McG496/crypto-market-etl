from src.notifications.slack_notifier import send_slack_alert
from src.load.alerts_loader import load_pending_alerts
from src.load.alerts_loader import mark_alert_notified
from src.utils.db import get_connection

def run_notification_pipeline():
    pending_alerts = load_pending_alerts()

    if pending_alerts.empty:
        return

    conn = get_connection()

    for _, alert in pending_alerts.iterrows():

        success = send_slack_alert(alert)

        if success:
            mark_alert_notified(conn, alert["id"])
