from datetime import datetime

from pydantic import BaseModel


class IncidentRead(BaseModel):
    id: int
    org_id: int
    incident_type: str
    status: str
    severity: str
    confidence: float
    first_seen_at: datetime


class IncidentCreate(BaseModel):
    org_id: int
    incident_type: str
    status: str = "new"
    severity: str = "medium"
    confidence: float = 0.6
