from src.transform.market_data_transform import run_transform, save_processed_data
from src.transform.sentiment_transform import run_fear_greed_transform, save_fear_greed_processed_data
from src.load.postgres_loader import load_market_data
from src.utils.logger import get_logger
from src.config.settings import COIN_LIST
import time

logger = get_logger(__name__)

def run_market_pipeline(metrics):
    start = time.perf_counter()

    logger.info("Starting market data pipeline")

    market_df = run_transform(COIN_LIST)
    metrics.market_rows = len(market_df)
    save_processed_data(market_df)

    logger.info("Market data transform completed in %.2fs", time.perf_counter() - start)

    load_market_data(market_df)

    sentiment_df = run_fear_greed_transform()
    save_fear_greed_processed_data(sentiment_df)

    logger.info("Market data pipeline completed")

    return market_df, sentiment_df