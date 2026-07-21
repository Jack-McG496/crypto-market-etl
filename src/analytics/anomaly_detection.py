from src.config.settings import ANOMALY_DETECTION_THRESHOLD
from src.utils.logger import get_logger
import pandas as pd

logger = get_logger(__name__)

def detect_anomalies(df: pd.DataFrame, sentiment_score, sentiment_label) -> pd.DataFrame:
    """
    Receives panda dataframe, sentiment details
    Returns a data frame with anomalies detected based on the sentiment parameters.
    """
    logger.info("Start anomaly detection")
    threshold = ANOMALY_DETECTION_THRESHOLD

    # Validate input
    if "z_score" not in df.columns:
        raise ValueError("z_score column missing from analytics dataframe")

    # Adjust sensitivity based on sentiment
    if sentiment_score >= 80:       # Extreme greed
        threshold = 2.5
    elif sentiment_score <= 20:     # Extreme fear
        threshold = 2.0

    df["is_anomalous"] = df["z_score"].abs() > threshold
    df["threshold"] = threshold

    # Add sentiment context
    df["sentiment_score"] = sentiment_score
    df["sentiment_label"] = sentiment_label

    logger.info(
        "Anomaly detection completed | threshold=%.2f | sentiment=%s (%s)",
        threshold,
        sentiment_score,
        sentiment_label,
    )
    return df
