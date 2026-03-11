from datetime import datetime

from pydantic import BaseModel


class IngestionRunRead(BaseModel):
    id: int
    started_at: datetime
    finished_at: datetime
    status: str
    total_raw: int
    total_normalized: int
    total_deduped: int
    total_persisted: int
    total_unmatched: int
    total_skipped_duplicates: int
    total_organizations_created: int
