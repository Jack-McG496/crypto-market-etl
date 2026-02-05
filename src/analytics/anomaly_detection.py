from src.utils.logger import get_logger

logger = get_logger(__name__)

def detect_anomalies(df, sentiment_score, sentiment_label):
    logger.info("Start anomaly detection")
    threshold = 3

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
