import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")


def load_latest_fear_greed_file() -> dict:
    """
    Load the latest raw fear and greed JSON file.
    """

    files = sorted(
        RAW_DATA_DIR.glob("fear_greed_index_*.json"),
        reverse=True
    )

    if not files:
        raise FileNotFoundError("No fear and greed raw files found")

    with open(files[0]) as f:
        return json.load(f)


def transform_fear_greed(raw_json: dict) -> dict:
    """
    Transform raw fear and greed JSON into a flat dict.
    """
    value = int(raw_json["data"][0]["value"])
    classification = raw_json["data"][0]["value_classification"]

    return {
        "sentiment_score": value,  # 0–100
        "sentiment_label": classification,  # Fear / Greed
        "is_extreme": value <= 20 or value >= 80
    }


def run_fear_greed_transform() -> pd.DataFrame:
    """
    Run transform and return a DataFrame.
    """
    logger.info("Starting fear and greed data transformation")

    rows = []
    raw_data = load_latest_fear_greed_file()
    try:
        transformed = transform_fear_greed(raw_data)
        rows.append(transformed)
    except KeyError as e:
        logger.warning(f"Missing expected field: {e}")
        raise


    df = pd.DataFrame(rows)
    logger.info(f"Transformation of fear and greed complete: {len(df)} rows")
    return df

def save_fear_greed_processed_data(df: pd.DataFrame):
    """
    Save processed fear and greed data to CSV.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = PROCESSED_DATA_DIR / f"sentiment_data_{timestamp}.csv"

    df.to_csv(file_path, index=False)
    print(f"Processed data saved to {file_path}")