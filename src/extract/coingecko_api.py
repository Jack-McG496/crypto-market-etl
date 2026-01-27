# Step 1: Extract Bitcoin price + volume from CoinGecko and save the raw JSON to disk
import requests
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

# fetch
def fetch_coin_market_data(coin_id: str):
    """
        Fetch current market data from CoinGecko API.
        Returns raw JSON response.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"

    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }

    logger.info(f"Fetching CoinGecko market data for {coin_id}")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Timeout while fetching CoinGecko market data for {coin_id}")
        raise
    except requests.exceptions.HTTPError:
        logger.error("HTTP Error while fetching CoinGecko market data for {coin_id}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error("Request error while fetching CoinGecko market data for {coin_id}")
        raise

    logger.info(f"Fetched CoinGecko market data for {coin_id}")
    return response.json()

# store
def save_raw_json(data: dict, source_name: str):
    """
    Save raw API response to data/raw with timestamped filename.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    raw_data_dir = Path("data/raw")
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_data_dir / f"{source_name}_market_data_{timestamp}.json"

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Raw data saved to {file_path}")


COINS = ["bitcoin", "ethereum"]
if __name__ == "__main__":
    for coin in COINS:
        raw_data = fetch_coin_market_data(coin)
        save_raw_json(raw_data, coin)