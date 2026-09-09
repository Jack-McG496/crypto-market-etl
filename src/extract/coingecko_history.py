import requests
import time
from datetime import datetime
from src.utils.logger import get_logger
from src.config.settings import COINGECKO_BASE_URL, COINGECKO_API_KEY, COINGECKO_REQUEST_TIMEOUT, RATE_LIMIT_SLEEP_TIME

logger = get_logger(__name__)

def fetch_historical_prices(coin_id: str, days=90) -> list:
    """
    Fetch historical market data for a coin.
    Returns hourly/daily prices depending on range.
    """

    logger.info(f"Fetching {days} days history for {coin_id}")

    base = COINGECKO_BASE_URL
    # If a CoinGecko PRO API key is provided, prefer the pro base URL when the
    # configured base is the public API. This avoids 400 errors when a pro key
    # is presented to the public endpoint.
    base_str = str(base or "")
    if COINGECKO_API_KEY and "pro-api" not in base_str and "api.coingecko.com" in base_str:
        base = "https://pro-api.coingecko.com/api/v3"

    url = f"{base}/coins/{coin_id}/market_chart"

    params = {
        "vs_currency": "usd",
        "days": days
    }

    headers = {}
    if COINGECKO_API_KEY:
        headers["x-cg-pro-api-key"] = COINGECKO_API_KEY

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=COINGECKO_REQUEST_TIMEOUT,
    )

    # Debug output
    print("Status:", response.status_code)
    print("Response:", response.text[:500])

    # Some CoinGecko API keys (demo vs pro) require using a different root URL.
    # If the provider returns a 400 with a message suggesting switching the
    # root URL, attempt the request again with the alternative base.
    if response.status_code == 400:
        try:
            body = response.json()
            msg = body.get("status", {}).get("error_message", "") or body.get("error_message", "")
        except Exception:
            msg = response.text

        if "change your root URL" in str(msg):
            # flip between pro and public endpoints
            alt_base = (
                "https://api.coingecko.com/api/v3"
                if "pro-api" in url
                else "https://pro-api.coingecko.com/api/v3"
            )
            alt_url = f"{alt_base}/coins/{coin_id}/market_chart"
            headers_alt = headers.copy()
            # retry the alternate URL once
            response = requests.get(
                alt_url,
                params=params,
                headers=headers_alt,
                timeout=COINGECKO_REQUEST_TIMEOUT,
            )
            print("Retry Status:", response.status_code)
            print("Retry Response:", response.text[:500])

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
