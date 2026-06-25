from src.utils.logger import get_logger
import numpy as np
import pandas as pd

logger = get_logger(__name__)


def calculate_volatility_features(df, window=24):
    logger.info("Start volatility feature calculation")

    df = df.copy()

    # Ensure correct ordering
    df = df.sort_values(["coin_id", "timestamp_utc"])

    logger.info(f"Input rows: {len(df)}")

    # Returns
    df["returns"] = (
        df.groupby("coin_id")["price_usd"]
        .pct_change()
    )

    # Rolling volatility
    df["rolling_std"] = (
        df.groupby("coin_id")["returns"]
        .transform(lambda x: x.rolling(window, min_periods=10).std())
    )

    # Z-score
    df["z_score"] = df["returns"] / df["rolling_std"]

    # Remove unusable rows
    df = df.dropna(subset=["z_score"])

    logger.info(f"Volatility features calculated: {len(df)} rows")

    return df


