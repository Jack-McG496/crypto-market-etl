from src.extract.coingecko_history import backfill_coins
from src.load.history_loader import load_historical_data
from src.utils.logger import get_logger
from src.config.settings import BACKFILL_DAYS, COIN_LIST

logger = get_logger(__name__)
coins = COIN_LIST

def main():

    logger.info("Starting historical backfill")

    data = backfill_coins(coins, days=BACKFILL_DAYS)

    load_historical_data(data)

    logger.info("Backfill finished successfully")


if __name__ == "__main__":
    main()
