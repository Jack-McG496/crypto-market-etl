import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class PipelineMetrics:
    run_id: Optional[str] = None
    market_rows: int = 0
    analytics_rows: int = 0
    alerts_generated: int = 0
    notifications_sent: int = 0
    notifications_failed: int = 0
    rows_ingested: int = 0
    retries: int = 0
    freshness_lag: Optional[float] = None
    last_successful_run: Optional[str] = None
    run_duration: float = 0.0
    duration_seconds: float = field(default=0.0, repr=False)
    status: str = "running"

    def __post_init__(self) -> None:
        if self.duration_seconds == 0.0 and self.run_duration:
            self.duration_seconds = self.run_duration
        elif self.run_duration == 0.0 and self.duration_seconds:
            self.run_duration = self.duration_seconds

    def as_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "market_rows": self.market_rows,
            "analytics_rows": self.analytics_rows,
            "alerts_generated": self.alerts_generated,
            "notifications_sent": self.notifications_sent,
            "notifications_failed": self.notifications_failed,
            "rows_ingested": self.rows_ingested,
            "retries": self.retries,
            "freshness_lag": self.freshness_lag,
            "last_successful_run": self.last_successful_run,
            "run_duration": self.run_duration,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
        }

    def to_db_row(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_duration": self.run_duration or self.duration_seconds,
            "freshness_lag": self.freshness_lag,
            "rows_ingested": self.rows_ingested,
            "retries": self.retries,
            "last_successful_run": self.last_successful_run,
            "market_rows": self.market_rows,
            "analytics_rows": self.analytics_rows,
            "alerts_generated": self.alerts_generated,
            "notifications_sent": self.notifications_sent,
            "notifications_failed": self.notifications_failed,
            "status": self.status,
        }

    def __str__(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, default=str)

