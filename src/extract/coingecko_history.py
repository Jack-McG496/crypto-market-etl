import requests
import time
from datetime import datetime
from src.utils.logger import get_logger
import os

logger = get_logger(__name__)

BASE_URL = "https://api.coingecko.com/api/v3"


def fetch_historical_prices(coin_id, days=90):
    """
    Fetch historical market data for a coin.
    Returns hourly/daily prices depending on range.
    """

    logger.info(f"Fetching {days} days history for {coin_id}")

    url = f"{BASE_URL}/coins/{coin_id}/market_chart"

    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "hourly"
    }

    headers = {
        "x-cg-pro-api-key": os.getenv("COINGECKO_API_KEY")
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()

    data = response.json()

    prices = data.get("prices", [])
    volumes = data.get("total_volumes", [])

    records = []

    for i in range(len(prices)):
        ts_ms = prices[i][0]
        price = prices[i][1]
        volume = volumes[i][1] if i < len(volumes) else None

        ts = datetime.utcfromtimestamp(ts_ms / 1000)

        records.append({
            "coin_id": coin_id,
            "timestamp_utc": ts,
            "price_usd": price,
            "volume_24h": volume
        })

    logger.info(f"Fetched {len(records)} rows for {coin_id}")

    time.sleep(1.2)  # rate limit safety

    return records


def backfill_coins(coins, days=90):

    all_data = []

    for coin in coins:
        data = fetch_historical_prices(coin, days)
        all_data.extend(data)

    logger.info(f"Backfill complete: {len(all_data)} rows")

    return all_data
