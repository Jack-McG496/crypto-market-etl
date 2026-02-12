from src.extract.coingecko_api import fetch_coin_market_data, save_raw_json
from src.extract.fear_greed_api import fetch_fear_greed_index, save_raw_json as save_fg_json
from src.transform.market_data_transform import run_transform, save_processed_data
from src.transform.sentiment_transform import run_fear_greed_transform, save_fear_greed_processed_data
from src.analytics.volatility_analysis import calculate_volatility_features
from src.analytics.anomaly_detection import detect_anomalies
from src.utils.logger import get_logger
from src.load.postgres_loader import load_market_data
from src.load.analytics_loader import load_analytics_data
from src.analytics.data_loader import load_price_history
from src.backfill import main as run_backfill
import os
from dotenv import load_dotenv
load_dotenv()

RUN_BACKFILL = os.getenv("RUN_BACKFILL") == "true"

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
        # 0. Backfill (run once or scheduled)
        if RUN_BACKFILL:
            run_backfill()

        # 1. Extract
        run_coingecko()
        run_fear_greed()

        # 2. Load snapshot
        market_df = run_transform(["bitcoin", "ethereum"])
        save_processed_data(market_df)
        ## Load base market snapshot into DB
        load_market_data(market_df)

        # 3. Transform sentiment
        sentiment_df = run_fear_greed_transform()
        ## Save sentiment to csv (for history)
        save_fear_greed_processed_data(sentiment_df)

        sentiment_score = sentiment_df["sentiment_score"].iloc[-1]
        sentiment_label = sentiment_df["sentiment_label"].iloc[-1]

        # 4. Analytics from DB
        price_df = load_price_history(days=90)

        analytics_df = calculate_volatility_features(price_df)

        alerts_df = detect_anomalies(
            analytics_df,
            sentiment_score,
            sentiment_label
        )

        # 5. Store alerts
        load_analytics_data(alerts_df)

        logger.info("ETL pipeline finished successfully")

    except Exception:
        logger.exception("ETL pipeline failed")
        raise

if __name__ == "__main__":
    main()
