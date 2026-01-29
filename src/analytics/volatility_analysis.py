import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)

def calculate_volatility_features(df, window=24):
    logger.info("Start volatility feature calculation")
    df = df.sort_values("timestamp_utc")

    df["returns"] = (
        df.groupby("coin_id")["price_usd"]
          .pct_change()
    )

    df["rolling_std"] = (
        df.groupby("coin_id")["returns"]
          .rolling(window)
          .std()
          .reset_index(level=0, drop=True)
    )

    df["z_score"] = df["returns"] / df["rolling_std"]
    logger.info("End volatility feature calculation")
    return df
