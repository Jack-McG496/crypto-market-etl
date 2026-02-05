from src.utils.logger import get_logger
import numpy as np

logger = get_logger(__name__)


def calculate_volatility_features(df, window: int = 24):
    """
    Calculate rolling volatility features and normalized returns (z-scores)
    for each crypto asset.
    """

    logger.info("Starting volatility feature calculation (window=%s)", window)

    # Validate input
    required_cols = {"coin_id", "timestamp_utc", "price_usd"}

    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Ensure correct ordering
    df = df.sort_values(["coin_id", "timestamp_utc"]).copy()

    # Returns
    df["returns"] = (
        df.groupby("coin_id")["price_usd"]
          .pct_change()
    )

    # Rolling volatility
    df["rolling_std"] = (
        df.groupby("coin_id")["returns"]
          .rolling(window, min_periods=window)
          .std()
          .reset_index(level=0, drop=True)
    )

    # Prevent division by zero
    df["rolling_std"] = df["rolling_std"].replace(0, np.nan)

    # Normalized returns
    df["z_score"] = df["returns"] / df["rolling_std"]

    # Metadata
    df["volatility_window"] = window

    logger.info(
        "Volatility feature calculation completed | window=%s",
        window
    )

    return df
