from src.extract.coingecko_api import fetch_coin_market_data, save_raw_json
from src.extract.fear_greed_api import fetch_fear_greed_index, save_raw_json as save_fg_json
from src.transform.market_data_transform import run_transform, save_processed_data
from src.transform.sentiment_transform import run_fear_greed_transform, save_fear_greed_processed_data
from src.analytics.volatility_analysis import calculate_volatility_features
from src.analytics.anomaly_detection import detect_anomalies
from src.utils.logger import get_logger
from src.load.postgres_loader import load_market_data
from src.load.analytics_loader import load_analytics_data
from src.alerts.alert_engine import generate_alerts
from src.load.alerts_loader import load_alert_data
import pandas as pd
from dotenv import load_dotenv
from src.analytics.data_loader import load_price_history
from src.analytics.regime_detection import classify_volatility_regime

load_dotenv()

logger = get_logger(__name__)

def run_coingecko():
    logger.info("Starting CoinGecko extraction")

    coins = ["bitcoin", "ethereum"]

    for coin in coins:
        try:
            data = fetch_coin_market_data(coin)
            save_raw_json(data, source_name=f"coingecko_{coin}")
        except Exception:
            logger.error(f"Failed to fetch data for {coin}")

    logger.info("CoinGecko extraction completed")


def run_fear_greed():
    logger.info("Starting Fear and Greed extraction")

    try:
        data = fetch_fear_greed_index(limit=1)
        save_fg_json(data)
    except Exception:
        logger.error("Failed to fetch Fear & Greed Index")

logger.info("Fear & Greed extraction completed")

def main():
    logger.info("ETL pipeline started")

    try:
        # Extract
        run_coingecko()
        run_fear_greed()

        # Transform
        market_df = run_transform(["bitcoin", "ethereum"])
        save_processed_data(market_df)

        sentiment_df = run_fear_greed_transform()
        save_fear_greed_processed_data(sentiment_df)

        # Load base market
        load_market_data(market_df)

        # Load historical prices from DB
        price_df = load_price_history(days=90)

        analytics_df = calculate_volatility_features(price_df)

        sentiment_score = sentiment_df["sentiment_score"].iloc[-1]
        sentiment_label = sentiment_df["sentiment_label"].iloc[-1]

        logger.info(f"Rows entering anomaly detection: {len(analytics_df)}")

        analytics_anomaly_df = detect_anomalies(
            analytics_df,
            sentiment_score,
            sentiment_label
        )

        analytics_anomaly_df = classify_volatility_regime(analytics_anomaly_df)

        logger.info(f"Analytics rows produced: {len(analytics_anomaly_df)}")
        logger.info(f"Analytics columns: {analytics_anomaly_df.columns.tolist()}")

        # Load analytics
        load_analytics_data(analytics_anomaly_df)

        alerts_df = generate_alerts(analytics_anomaly_df)
        # Load alerts
        load_alert_data(alerts_df)


        logger.info("ETL pipeline finished successfully")

    except Exception:
        logger.exception("ETL pipeline failed")
        raise




logger.info("ETL pipeline finished successfully")

if __name__ == "__main__":
    main()
