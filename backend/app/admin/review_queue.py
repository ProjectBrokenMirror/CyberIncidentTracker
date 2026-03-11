from dataclasses import dataclass


@dataclass
class ReviewItem:
    incident_id: int
    reason: str
    suggested_org_id: int | None
    confidence: float
