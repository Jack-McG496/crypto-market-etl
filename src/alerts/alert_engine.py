import pandas as pd
from datetime import datetime
from src.main import metrics
from src.utils import logger

logger = logger.get_logger(__name__)

def generate_alerts(df):

    if df.empty:
        logger.warning("No data available for alert generation.")
        return pd.DataFrame(columns=[
            "coin_id",
            "alert_type",
            "severity",
            "message",
            "created_at",
            "analytics_timestamp"
        ])

    alerts = []

    # Volatility alerts
    anomalous = df[df["is_anomalous"] == True]

    for _, row in anomalous.iterrows():

        alerts.append({
            "coin_id": row["coin_id"],
            "alert_type": "VOLATILITY",
            "severity": "WARNING",
            "message": f"{row['coin_id']} volatility exceeded threshold",
            "created_at": datetime.utcnow(),
            "analytics_timestamp": row["timestamp_utc"]
        })

    # Regime alerts
    df = df.sort_values(["coin_id", "timestamp_utc"])

    df["previous_regime"] = (
        df.groupby("coin_id")["volatility_regime"]
            .shift(1)
    )

    regime_changes = df[
        (df["previous_regime"].notna()) &
        (df["previous_regime"] != df["volatility_regime"])
        ]

    for _, row in regime_changes.iterrows():
        severity = "INFO"

        if row["volatility_regime"] == "High":
            severity = "WARNING"

        if row["volatility_regime"] == "Extreme":
            severity = "CRITICAL"

        alerts.append({
            "coin_id": row["coin_id"],
            "alert_type": "REGIME_CHANGE",
            "severity": severity,
            "message": (
                f"{row['coin_id']} regime changed "
                f"from {row['previous_regime']} "
                f"to {row['volatility_regime']}"
            ),
            "created_at": datetime.utcnow(),
            "analytics_timestamp": row["timestamp_utc"]
        })

    # Sentiment alerts
    latest = df.sort_values("timestamp_utc").iloc[-1]

    if latest["sentiment_score"] <= 20:
        alerts.append({
            "coin_id": "MARKET",
            "alert_type": "SENTIMENT",
            "severity": "WARNING",
            "message": (
                f"Extreme Fear detected "
                f"({latest['sentiment_score']})"
            ),
            "created_at": datetime.utcnow(),
            "analytics_timestamp": latest["timestamp_utc"]
        })

    if latest["sentiment_score"] >= 80:
        alerts.append({
            "coin_id": "MARKET",
            "alert_type": "SENTIMENT",
            "severity": "WARNING",
            "message": (
                f"Extreme Greed detected "
                f"({latest['sentiment_score']})"
            ),
            "created_at": datetime.utcnow(),
            "analytics_timestamp": latest["timestamp_utc"]
        })

    metrics.alerts_generated = len(alerts)
    logger.info(f"Number of alert rows produced: {len(alerts)}")


    return pd.DataFrame(alerts)