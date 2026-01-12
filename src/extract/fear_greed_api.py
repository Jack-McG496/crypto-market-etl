import requests
import json
from datetime import datetime
from pathlib import Path


def fetch_fear_greed_index(limit: int = 1):
    """
    Fetch Crypto Fear & Greed Index data.
    Returns raw JSON response.
    """
    url = "https://api.alternative.me/fng/"

    params = {
        "limit": limit,
        "format": "json"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


def save_raw_json(data: dict):
    """
    Save raw API response to data/raw with timestamped filename.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    raw_data_dir = Path("data/raw")
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_data_dir / f"fear_greed_index_{timestamp}.json"

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Raw data saved to {file_path}")


if __name__ == "__main__":
    fg_data = fetch_fear_greed_index(limit=1)
    save_raw_json(fg_data)
