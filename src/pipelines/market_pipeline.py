from src.transform.market_data_transform import run_transform, save_processed_data
from src.transform.sentiment_transform import run_fear_greed_transform, save_fear_greed_processed_data
from src.load.postgres_loader import load_market_data
from src.utils.logger import get_logger
from src.config.settings import COIN_LIST

logger = get_logger(__name__)

def run_market_pipeline():

    market_df = run_transform(COIN_LIST)
    save_processed_data(market_df)

    load_market_data(market_df)

    sentiment_df = run_fear_greed_transform()
    save_fear_greed_processed_data(sentiment_df)

    return market_df, sentiment_df