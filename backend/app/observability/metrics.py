from dataclasses import dataclass


@dataclass
class IngestionMetrics:
    connector_success_rate: float = 0.0
    ingest_lag_minutes_p95: float = 0.0
    duplicate_rate: float = 0.0
