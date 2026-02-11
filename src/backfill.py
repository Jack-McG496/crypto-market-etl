from src.extract.coingecko_history import backfill_coins
from src.load.history_loader import load_historical_data
from src.utils.logger import get_logger
from dotenv import load_dotenv
load_dotenv()

logger = get_logger(__name__)


def main():

    coins = ["bitcoin", "ethereum"]

    logger.info("Starting historical backfill")

    data = backfill_coins(coins, days=90)

    load_historical_data(data)

    logger.info("Backfill finished successfully")


if __name__ == "__main__":
    main()
