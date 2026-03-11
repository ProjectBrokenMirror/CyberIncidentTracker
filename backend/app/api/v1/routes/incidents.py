from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentRead

router = APIRouter()


@router.get("/")
def list_incidents(db: Session = Depends(get_db)) -> dict[str, list[IncidentRead]]:
    items = db.execute(select(Incident).order_by(Incident.id.desc()).limit(100)).scalars().all()
    return {"items": [IncidentRead.model_validate(item, from_attributes=True) for item in items]}


@router.post("/", response_model=IncidentRead)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> IncidentRead:
    incident = Incident(
        org_id=payload.org_id,
        incident_type=payload.incident_type,
        status=payload.status,
        severity=payload.severity,
        confidence=payload.confidence,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return IncidentRead.model_validate(incident, from_attributes=True)


@router.get("/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> IncidentRead:
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentRead.model_validate(incident, from_attributes=True)
