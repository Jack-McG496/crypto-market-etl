from src.extract.coingecko_api import fetch_coin_market_data, save_raw_json
from src.extract.fear_greed_api import fetch_fear_greed_index, save_raw_json as save_fg_json
from src.transform.market_data_transform import run_transform, save_processed_data
from utils.logger import get_logger

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
        run_coingecko()
        run_fear_greed()
        df = run_transform(["bitcoin", "ethereum"])
        save_processed_data(df)
    except Exception as e:
        logger.exception("ETL pipeline failed")
    raise


logger.info("ETL pipeline finished successfully")

if __name__ == "__main__":
    main()
