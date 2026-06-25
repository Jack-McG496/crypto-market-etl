from src.utils.logger import get_logger

logger = get_logger(__name__)


def classify_volatility_regime(df):
    logger.info("Classifying volatility regimes")

    if "z_score" not in df.columns:
        raise ValueError("z_score column missing")

    def regime(z, threshold):
        if z is None:
            return "Unknown"

        z = abs(z)

        if z < 1:
            return "Calm"
        elif z < 2:
            return "Elevated"
        elif z < threshold:
            return "High"
        else:
            return "Extreme"

    df["volatility_regime"] = df.apply(
        lambda row: regime(row["z_score"], row["threshold"]),
        axis=1
    )

    logger.info("Volatility regime classification complete")

    return df
