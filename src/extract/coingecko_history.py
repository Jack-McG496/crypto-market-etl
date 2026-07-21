import requests
import time
from datetime import datetime
from src.utils.logger import get_logger
from src.config.settings import COINGECKO_BASE_URL, COINGECKO_API_KEY, COINGECKO_REQUEST_TIMEOUT, COINGECKO_REQUEST_PARAMETERS, RATE_LIMIT_SLEEP_TIME

logger = get_logger(__name__)

def fetch_historical_prices(coin_id: str, days=90) -> list:
    """
    Fetch historical market data for a coin.
    Returns hourly/daily prices depending on range.
    """

    logger.info(f"Fetching {days} days history for {coin_id}")

    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"

    params = {
        "vs_currency": "usd",
        "days": days
    }

    headers = {
        "x-cg-pro-api-key": COINGECKO_API_KEY
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=COINGECKO_REQUEST_TIMEOUT
    )

    print("Status:", response.status_code)
    print("Response:", response.text[:500])  # debug

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

    time.sleep(RATE_LIMIT_SLEEP_TIME)  # rate limit safety

    return records


def backfill_coins(coins: list, days=90) -> list:

    all_data = []

    for coin in coins:
        data = fetch_historical_prices(coin, days)
        all_data.extend(data)

    logger.info(f"Backfill complete: {len(all_data)} rows")

    return all_data
