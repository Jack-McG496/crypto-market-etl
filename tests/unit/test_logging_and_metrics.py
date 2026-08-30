import logging
import sqlite3

from src.pipelines.metrics import PipelineMetrics
from src.pipelines.metrics_writer import persist_run_metrics
from src.utils.logger import get_logger


def test_logger_includes_run_context(caplog):
    logger = get_logger(
        "unit.test.logger",
        run_id="run-123",
        stage="extract",
        coin_id="btc",
        task="fetch_market",
    )

    with caplog.at_level(logging.INFO):
        logger.info("market fetch ok")

    assert any(
        "run_id=run-123" in rec.message
        and "stage=extract" in rec.message
        and "coin_id=btc" in rec.message
        and "task=fetch_market" in rec.message
        for rec in caplog.records
    )


def test_metrics_export_and_persistence(tmp_path):
    metrics = PipelineMetrics(
        run_id="run-456",
        run_duration=12.5,
        rows_ingested=42,
        retries=3,
        freshness_lag=90.0,
        last_successful_run="2026-08-29T10:00:00Z",
    )

    db_path = tmp_path / "pipeline_metrics.sqlite"
    persist_run_metrics(metrics, db_path=db_path)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT run_id, rows_ingested, retries, freshness_lag, last_successful_run FROM pipeline_runs WHERE run_id = ?",
            ("run-456",),
        ).fetchone()

    assert row is not None
    assert row[0] == "run-456"
    assert row[1] == 42
    assert row[2] == 3
    assert row[3] == 90.0
    assert row[4] == "2026-08-29T10:00:00Z"
