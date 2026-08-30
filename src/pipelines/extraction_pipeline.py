from src.extract.coingecko_api import fetch_coin_market_data, save_raw_json, PermanentAPIError
from src.extract.fear_greed_api import fetch_fear_greed_index, save_raw_json as save_fg_json
from src.utils.logger import get_logger
from src.config.settings import COIN_LIST
import time

logger = get_logger(__name__)

coins = COIN_LIST


def run_extraction_pipeline(run_id: str | None = None):
    start = time.perf_counter()
    logger = get_logger(__name__, run_id=run_id, stage="extract", task="extraction_pipeline")

    logger.info("Starting extraction pipeline")

    for coin in coins:
        try:
            data = fetch_coin_market_data(coin, run_id=run_id)
        except PermanentAPIError as exc:
            logger.error("Permanent failure fetching %s: %s", coin, exc, extra={"coin_id": coin, "task": "fetch_market"})
            continue
        except Exception:
            logger.exception("Unexpected error fetching %s; skipping", coin, extra={"coin_id": coin, "task": "fetch_market"})
            continue

        save_raw_json(data, source_name=f"coingecko_{coin}")

    logger.info("CoinGecko extraction completed in %.2fs", time.perf_counter() - start)

    start = time.perf_counter()
    try:
        fg_data = fetch_fear_greed_index(limit=1, run_id=run_id)
    except Exception:
        logger.exception("Unexpected error fetching fear and greed index; skipping")
        fg_data = None

    if fg_data is not None:
        save_fg_json(fg_data)

    logger.info("Extraction pipeline completed")