import json
import pytest
from pathlib import Path

from src.transform import market_data_transform as mdt
from src.extract import coingecko_api as cg


def _write_raw(tmp_path: Path, coin: str, payload: dict) -> Path:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    fn = raw_dir / f"coingecko_{coin}_market_data_20260101_000000.json"
    fn.write_text(json.dumps(payload), encoding="utf-8")
    return fn


def test_success_transform_adds_metadata_and_computes_ratio(monkeypatch, tmp_path):
    monkeypatch.setattr(mdt, "RAW_DATA_DIR", tmp_path / "raw")
    monkeypatch.setattr(cg, "DEAD_LETTER_DIR", tmp_path / "dead")
    payload = {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "market_data": {
            "current_price": {"usd": 30000},
            "market_cap": {"usd": 600000000},
            "total_volume": {"usd": 30000000},
            "circulating_supply": 19000000,
            "price_change_percentage_24h": 1.23,
        },
    }
    _write_raw(tmp_path, "bitcoin", payload)

    df = mdt.run_transform(["bitcoin"], run_id="test-run-1")
    assert len(df) == 1
    row = df.iloc[0]
    assert row["coin_id"] == "bitcoin"
    assert row["source"] == "coingecko"
    assert row["run_id"] == "test-run-1"
    assert "raw_file" in row and row["raw_file"] is not None
    # volume_to_marketcap = total_volume / market_cap = 30e6 / 600e6 = 0.05
    assert pytest.approx(0.05, rel=1e-3) == row["volume_to_marketcap"]


def test_missing_top_level_writes_dead_letter_and_skips(monkeypatch, tmp_path):
    monkeypatch.setattr(mdt, "RAW_DATA_DIR", tmp_path / "raw")
    monkeypatch.setattr(cg, "DEAD_LETTER_DIR", tmp_path / "dead")
    # payload missing 'market_data'
    payload = {"id": "missingcoin", "symbol": "mc", "name": "MissingCoin"}
    _write_raw(tmp_path, "missingcoin", payload)

    df = mdt.run_transform(["missingcoin"])
    assert len(df) == 0

    dl_files = list((tmp_path / "dead").glob("*_deadletter_*.json"))
    assert dl_files, "dead-letter file should be created for invalid raw payload"
    body = json.loads(dl_files[0].read_text(encoding="utf-8"))
    assert body["source"] in ("missingcoin", "unknown")
    assert "Missing top-level keys" in body["error"]


def test_zero_market_cap_sets_volume_ratio_none(monkeypatch, tmp_path):
    monkeypatch.setattr(mdt, "RAW_DATA_DIR", tmp_path / "raw")
    monkeypatch.setattr(cg, "DEAD_LETTER_DIR", tmp_path / "dead")
    payload = {
        "id": "zerocap",
        "symbol": "zc",
        "name": "ZeroCap",
        "market_data": {
            "current_price": {"usd": 1.0},
            "market_cap": {"usd": 0},
            "total_volume": {"usd": 1000},
            "circulating_supply": 1000,
        },
    }
    _write_raw(tmp_path, "zerocap", payload)

    df = mdt.run_transform(["zerocap"])
    assert len(df) == 1
    row = df.iloc[0]
    assert row["market_cap_usd"] == 0.0
    assert row["volume_to_marketcap"] is None