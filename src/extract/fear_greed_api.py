from src.utils.logger import get_logger
from src.config.settings import FEAR_GREED_API_URL, FEAR_GREED_REQUEST_TIMEOUT
import requests
import json
from datetime import datetime
from pathlib import Path

logger = get_logger(__name__)

def fetch_fear_greed_index(limit: int = 1) -> json:
    """
        Fetch Crypto Fear & Greed Index data.
        Returns raw JSON response.
    """
    base_url = FEAR_GREED_API_URL.rstrip("/")
    url = f"{base_url}/?limit={limit}&format=json"

    response = requests.get(url, timeout=FEAR_GREED_REQUEST_TIMEOUT)
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

    logger.info(f"Raw data saved to {file_path}")


if __name__ == "__main__":
    fg_data = fetch_fear_greed_index(limit=1)
    save_raw_json(fg_data)
