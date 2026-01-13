import json
from pathlib import Path
from datetime import datetime
import pandas as pd


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")


def load_latest_coingecko_file(coin: str) -> dict:
    """
    Load the latest raw CoinGecko JSON file for a given coin.
    """
    files = sorted(
        RAW_DATA_DIR.glob(f"coingecko_{coin}_*.json"),
        reverse=True
    )

    if not files:
        raise FileNotFoundError(f"No raw files found for {coin}")

    with open(files[0]) as f:
        return json.load(f)


def transform_market_data(raw_data: dict) -> dict:
    """
    Transform raw CoinGecko JSON into a flat dict.
    """
    market = raw_data["market_data"]

    return {
        "coin_id": raw_data["id"],
        "symbol": raw_data["symbol"],
        "name": raw_data["name"],
        "timestamp_utc": datetime.utcnow(),
        "current_price_usd": market["current_price"]["usd"],
        "market_cap_usd": market["market_cap"]["usd"],
        "total_volume_usd": market["total_volume"]["usd"],
        "circulating_supply": market["circulating_supply"],
        "price_change_24h_pct": market["price_change_percentage_24h"],
    }


def run_transform(coins: list[str]) -> pd.DataFrame:
    """
    Run transform for multiple coins and return a DataFrame.
    """
    rows = []

    for coin in coins:
        raw_data = load_latest_coingecko_file(coin)
        transformed = transform_market_data(raw_data)
        rows.append(transformed)

    df = pd.DataFrame(rows)
    return df


def save_processed_data(df: pd.DataFrame):
    """
    Save processed market data to CSV.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = PROCESSED_DATA_DIR / f"market_data_{timestamp}.csv"

    df.to_csv(file_path, index=False)
    print(f"Processed data saved to {file_path}")
