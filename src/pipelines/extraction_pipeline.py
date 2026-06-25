from src.extract.coingecko_api import fetch_coin_market_data, save_raw_json
from src.extract.fear_greed_api import fetch_fear_greed_index, save_raw_json as save_fg_json
from src.utils.logger import get_logger

logger = get_logger(__name__)

def run_extraction_pipeline():

    logger.info("Starting extraction pipeline")

    coins = ["bitcoin", "ethereum"]

    for coin in coins:
        data = fetch_coin_market_data(coin)
        save_raw_json(data, source_name=f"coingecko_{coin}")

    fg_data = fetch_fear_greed_index(limit=1)
    save_fg_json(fg_data)

    logger.info("Extraction pipeline completed")