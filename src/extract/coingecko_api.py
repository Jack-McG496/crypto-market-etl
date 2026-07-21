import requests
import json
from datetime import datetime
from src.utils.logger import get_logger
from src.config.settings import COIN_LIST, COINGECKO_BASE_URL, COINGECKO_API_KEY, COINGECKO_REQUEST_TIMEOUT, COINGECKO_REQUEST_PARAMETERS, RAW_DATA_DIR 

logger = get_logger(__name__)

def fetch_coin_market_data(coin_id: str) -> json:
    """
        Fetch current market data from CoinGecko API.
        Returns raw JSON response.
    """
    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}"

    logger.info(f"Fetching CoinGecko market data for {coin_id}")

    try:
        headers = {
            "x-cg-pro-api-key": COINGECKO_API_KEY
        }

        response = requests.get(
            url,
            params=COINGECKO_REQUEST_PARAMETERS,
            headers=headers,
            timeout=COINGECKO_REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching CoinGecko market data for {coin_id}")
        raise
    except requests.exceptions.HTTPError:
        logger.error(f"HTTP Error while fetching CoinGecko market data for {coin_id}")
        raise
    except requests.exceptions.RequestException:
        logger.error(f"Request error while fetching CoinGecko market data for {coin_id}")
        raise

    logger.info(f"Fetched CoinGecko market data for {coin_id}")
    return response.json()

def save_raw_json(data: dict, source_name: str):
    """
        Save raw API response to data/raw with timestamped filename.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_path = RAW_DATA_DIR / f"{source_name}_market_data_{timestamp}.json"

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Raw data saved to {file_path}")


COINS = COIN_LIST
if __name__ == "__main__":
    for coin in COINS:
        raw_data = fetch_coin_market_data(coin)
        save_raw_json(raw_data, coin)