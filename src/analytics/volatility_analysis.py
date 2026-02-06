from src.utils.logger import get_logger
import numpy as np

logger = get_logger(__name__)


def calculate_volatility_features(df, window=24):

    logger.info("Start volatility feature calculation")

    df = df.sort_values(["coin_id", "timestamp_utc"])

    # Returns
    df["returns"] = (
        df.groupby("coin_id")["price_usd"]
          .pct_change()
    )

    # Rolling std (very permissive early)
    df["rolling_std"] = (
        df.groupby("coin_id")["returns"]
          .rolling(window, min_periods=2)
          .std()
          .reset_index(level=0, drop=True)
    )

    # Fallback: global std per coin (bootstrap)
    fallback_std = (
        df.groupby("coin_id")["returns"]
          .transform("std")
    )

    df["rolling_std"] = df["rolling_std"].fillna(fallback_std)

    # Avoid zero division
    df["rolling_std"] = df["rolling_std"].replace(0, None)

    # Z-score
    df["z_score"] = df["returns"] / df["rolling_std"]

    # Only drop rows with no returns
    df = df.dropna(subset=["returns"])

    logger.info(
        f"Volatility features calculated: {len(df)} rows"
    )

    return df

