import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)

def detect_anomalies(df, sentiment_score):
    logger.info("Start anomaly detection")

    # Adjust sensitivity based on sentiment
    if sentiment_score >= 80:       # Extreme greed
        threshold = 2.5
    elif sentiment_score <= 20:     # Extreme fear
        threshold = 2.0
    else:
        threshold = 3.0

    df["is_anomalous"] = df["z_score"].abs() > threshold
    df["threshold"] = threshold
    logger.info("End anomaly detection")
    return df
