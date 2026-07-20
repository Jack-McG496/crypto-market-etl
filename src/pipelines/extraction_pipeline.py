from src.extract.coingecko_api import fetch_coin_market_data, save_raw_json
from src.extract.fear_greed_api import fetch_fear_greed_index, save_raw_json as save_fg_json
from src.utils.logger import get_logger
from src.config.settings import COIN_LIST
from src.main import metrics
import time
logger = get_logger(__name__)

coins = COIN_LIST

def run_extraction_pipeline():
    start = time.perf_counter()

    logger.info("Starting extraction pipeline")

    for coin in coins:
        data = fetch_coin_market_data(coin)
        save_raw_json(data, source_name=f"coingecko_{coin}")

    logger.info("CoinGecko extraction completed in %.2fs", time.perf_counter() - start)

    start = time.perf_counter()
    fg_data = fetch_fear_greed_index(limit=1)
    logger.info("Fear and Greed extraction completed in %.2fs", time.perf_counter() - start)

    save_fg_json(fg_data)

    logger.info("Extraction pipeline completed")