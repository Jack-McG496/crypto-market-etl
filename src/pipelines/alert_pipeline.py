from src.alerts.alert_engine import generate_alerts
from src.load.alerts_loader import load_alert_data
from src.utils.logger import get_logger
import time
logger = get_logger(__name__)

def run_alert_pipeline(analytics_df):
    start = time.perf_counter()
    logger.info("Starting alerts pipeline")

    alerts_df = generate_alerts(analytics_df)
    load_alert_data(alerts_df)

    logger.info("Alerts generated in %.2fs", time.perf_counter() - start)

    logger.info("Alert pipeline complete")

    return alerts_df