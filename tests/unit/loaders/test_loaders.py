from datetime import datetime

from src.load.postgres_loader import normalize_market_record


def test_normalize_market_record_maps_ingestion_metadata():
    row = {
        "coin_id": "bitcoin",
        "price_usd": 50000,
        "total_volume_usd": 1000000,
        "market_cap_usd": 2000000,
        "timestamp_utc": datetime(2026, 1, 1, 12, 0, 0),
        "raw_file": "data/raw/bitcoin.json",
        "run_id": "run-123",
    }

    record = normalize_market_record(row)

    assert record[0] == "bitcoin"
    assert record[1] == 50000
    assert record[2] == 1000000
    assert record[3] == 2000000
    assert record[4] == datetime(2026, 1, 1, 12, 0, 0)
    assert record[5] is not None
    assert record[6] == "data/raw/bitcoin.json"
    assert record[7] == "run-123"
