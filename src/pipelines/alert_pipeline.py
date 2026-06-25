from src.alerts.alert_engine import generate_alerts
from src.load.alerts_loader import load_alert_data

def run_alert_pipeline(analytics_df):
    alerts_df = generate_alerts(analytics_df)
    load_alert_data(alerts_df)

    return alerts_df