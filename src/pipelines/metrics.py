from dataclasses import dataclass

@dataclass
class PipelineMetrics:
    market_rows: int = 0
    analytics_rows: int = 0
    alerts_generated: int = 0
    notifications_sent: int = 0
    notifications_failed: int = 0
    duration_seconds: float = 0.0

