from dataclasses import dataclass

@dataclass
class PipelineMetrics:

    def __init__(self):
        self.market_rows: int = 0
        self.analytics_rows: int = 0
        self.alerts_generated: int = 0
        self.notifications_sent: int = 0
        self.notifications_failed: int = 0
        self.duration_seconds: float = 0.0

