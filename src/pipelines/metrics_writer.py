import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union

from src.pipelines.metrics import PipelineMetrics

DEFAULT_DB_PATH = Path("data/metrics/pipeline_runs.sqlite")
DEFAULT_JSON_PATH = Path("data/metrics/latest_metrics.json")


def _ensure_parent(path: Union[str, Path]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def persist_run_metrics(metrics: PipelineMetrics, db_path: Union[str, Path] = DEFAULT_DB_PATH) -> Path:
    db_path = _ensure_parent(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                run_duration REAL,
                freshness_lag REAL,
                rows_ingested INTEGER,
                retries INTEGER,
                last_successful_run TEXT,
                market_rows INTEGER,
                analytics_rows INTEGER,
                alerts_generated INTEGER,
                notifications_sent INTEGER,
                notifications_failed INTEGER,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        row = metrics.to_db_row()
        conn.execute(
            """
            INSERT INTO pipeline_runs (
                run_id, run_duration, freshness_lag, rows_ingested, retries,
                last_successful_run, market_rows, analytics_rows, alerts_generated,
                notifications_sent, notifications_failed, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                run_duration = excluded.run_duration,
                freshness_lag = excluded.freshness_lag,
                rows_ingested = excluded.rows_ingested,
                retries = excluded.retries,
                last_successful_run = excluded.last_successful_run,
                market_rows = excluded.market_rows,
                analytics_rows = excluded.analytics_rows,
                alerts_generated = excluded.alerts_generated,
                notifications_sent = excluded.notifications_sent,
                notifications_failed = excluded.notifications_failed,
                status = excluded.status
            """,
            (
                row.get("run_id"),
                row.get("run_duration"),
                row.get("freshness_lag"),
                row.get("rows_ingested"),
                row.get("retries"),
                row.get("last_successful_run"),
                row.get("market_rows"),
                row.get("analytics_rows"),
                row.get("alerts_generated"),
                row.get("notifications_sent"),
                row.get("notifications_failed"),
                row.get("status"),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    export_json = _ensure_parent(DEFAULT_JSON_PATH)
    export_json.write_text(json.dumps(metrics.as_dict(), sort_keys=True, default=str), encoding="utf-8")
    return db_path


def fetch_pipeline_runs(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> list[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT run_id, run_duration, freshness_lag, rows_ingested, retries,
                   last_successful_run, market_rows, analytics_rows, alerts_generated,
                   notifications_sent, notifications_failed, status
            FROM pipeline_runs
            ORDER BY created_at DESC
            """
        ).fetchall()
    finally:
        conn.close()
    columns = [
        "run_id",
        "run_duration",
        "freshness_lag",
        "rows_ingested",
        "retries",
        "last_successful_run",
        "market_rows",
        "analytics_rows",
        "alerts_generated",
        "notifications_sent",
        "notifications_failed",
        "status",
    ]
    return [dict(zip(columns, row)) for row in rows]
