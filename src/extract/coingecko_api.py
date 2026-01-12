# Step 1: Extract Bitcoin price + volume from CoinGecko and save the raw JSON to disk
import requests
import json
from datetime import datetime
from pathlib import Path

# fetch
def fetch_bitcoin_market_data():
    """
        Fetch current Bitcoin market data from CoinGecko API.
        Returns raw JSON response.
    """
    url = "https://api.coingecko.com/api/v3/coins/bitcoin"

    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()

def fetch_ethereum_market_data():
    """
        Fetch current Bitcoin market data from CoinGecko API.
        Returns raw JSON response.
    """
    url = "https://api.coingecko.com/api/v3/coins/ethereum"

    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()

# store
def save_raw_json(data: dict):
    """
    Save raw API response to data/raw with timestamped filename.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    raw_data_dir = Path("data/raw")
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_data_dir / f"ethereum_market_data_{timestamp}.json"

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Raw data saved to {file_path}")


if __name__ == "__main__":
    ethereum_data = fetch_ethereum_market_data()
    save_raw_json(ethereum_data)