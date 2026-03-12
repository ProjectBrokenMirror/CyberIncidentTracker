from datetime import datetime

from pydantic import BaseModel


class VendorWatcherCreate(BaseModel):
    email: str
    is_active: bool = True


class VendorWatcherRead(BaseModel):
    id: int
    vendor_id: int
    email: str
    is_active: bool
    created_at: datetime


class AlertMetricsRead(BaseModel):
    total_events: int
    sent_events: int
    failed_events: int
    skipped_events: int
    last_24h_total: int
    last_24h_sent: int
    last_24h_failed: int
    last_24h_skipped: int
