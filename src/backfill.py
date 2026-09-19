from src.config.settings import BACKFILL_DAYS, COIN_LIST
from src.extract.coingecko_history import backfill_coins
from src.load.history_loader import load_historical_data
from src.utils.logger import get_logger

logger = get_logger(__name__)
coins = COIN_LIST

def main():

    logger.info("Starting historical backfill")

    if not coins:
        logger.error("No coins configured for backfill (COIN_LIST is empty). Aborting.")
        raise SystemExit(1)

    data = backfill_coins(coins, days=BACKFILL_DAYS)

    if not data:
        logger.warning("Backfill produced no rows; nothing to load into DB")
    else:
        load_historical_data(data)
        logger.info("Backfill loaded %d rows into DB", len(data))

    logger.info("Backfill finished successfully")


if __name__ == "__main__":
    main()
