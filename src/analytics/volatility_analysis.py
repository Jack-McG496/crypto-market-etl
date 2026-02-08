from src.utils.logger import get_logger
import numpy as np
import pandas as pd

logger = get_logger(__name__)


def calculate_volatility_features(df, window=24):

    logger.info("Start volatility feature calculation")
    logger.info(f"Input rows: {len(df)}")

    logger.info("Sample prices:")
    logger.info(df[["coin_id", "timestamp_utc", "price_usd"]].head(10))

    df = df.sort_values(["coin_id", "timestamp_utc"])

    # Returns
    df["price_usd"] = pd.to_numeric(df["price_usd"], errors="coerce")
    df["returns"] = (
        df.groupby("coin_id")["price_usd"]
          .pct_change()
    )
    logger.info("Returns sample:")
    logger.info(df[["coin_id", "returns"]].head(10))

    # Rolling std (very permissive early)
    df["rolling_std"] = (
        df.groupby("coin_id")["returns"]
          .rolling(window, min_periods=2)
          .std()
          .reset_index(level=0, drop=True)
    )

    if df["returns"].isna().all():
        logger.warning("Cold start: insufficient data for volatility")

        df["returns"] = 0
        df["rolling_std"] = 1
        df["z_score"] = 0

    logger.info("Rolling std sample:")
    logger.info(df[["coin_id", "rolling_std"]].head(10))

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

