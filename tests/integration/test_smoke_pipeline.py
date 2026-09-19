import os

import pandas as pd
import pytest

from src.pipelines import market_pipeline


@pytest.mark.smoke
@pytest.mark.integration
def test_market_pipeline_smoke(monkeypatch, db_connection):
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL is not set")

    with db_connection.cursor() as cur:
        cur.execute("DELETE FROM market_data")
        cur.execute("DELETE FROM pipeline_runs")
    db_connection.commit()

    market_df = pd.DataFrame(
        {
            "coin_id": ["btc_smoke", "btc_smoke"],
            "price_usd": [100.0, 101.0],
            "timestamp_utc": pd.to_datetime([
                "2026-02-01T00:00:00Z",
                "2026-02-01T01:00:00Z",
            ]),
            "market_cap": [1000.0, 1001.0],
            "volume_24h": [500.0, 510.0],
            "run_id": ["smoke-run", "smoke-run"],
        }
    )
    sentiment_df = pd.DataFrame({
        "sentiment_score": [65],
        "sentiment_label": ["Neutral"],
    })

    monkeypatch.setattr(market_pipeline, "run_transform", lambda coins, run_id=None: market_df)
    monkeypatch.setattr(market_pipeline, "save_processed_data", lambda df: None)
    monkeypatch.setattr(market_pipeline, "run_fear_greed_transform", lambda: sentiment_df)
    monkeypatch.setattr(market_pipeline, "save_fear_greed_processed_data", lambda df: None)

    loaded_market, loaded_sentiment = market_pipeline.run_market_pipeline(run_id="smoke-run")

    assert len(loaded_market) == 2
    assert len(loaded_sentiment) == 1

    count = pd.read_sql(
        "SELECT COUNT(*) FROM market_data WHERE coin_id = 'btc_smoke'",
        db_connection,
    ).iloc[0, 0]
    assert count == 2
