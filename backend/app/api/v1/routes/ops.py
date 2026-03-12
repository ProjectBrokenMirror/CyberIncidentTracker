from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit_event import AuditEvent
from app.models.ingestion_run import IngestionRun
from app.schemas.alerts import AlertMetricsRead
from app.schemas.audit import AuditEventRead
from app.schemas.ingestion import IngestionRunRead
from app.tasks.alerts import read_alert_metrics

router = APIRouter()


@router.get("/ingestion-runs")
def list_ingestion_runs(db: Session = Depends(get_db)) -> dict[str, list[IngestionRunRead]]:
    runs = db.execute(select(IngestionRun).order_by(IngestionRun.id.desc()).limit(50)).scalars().all()
    return {"items": [IngestionRunRead.model_validate(run, from_attributes=True) for run in runs]}


@router.get("/alerts/metrics", response_model=AlertMetricsRead)
def get_alert_metrics(db: Session = Depends(get_db)) -> AlertMetricsRead:
    return AlertMetricsRead(**read_alert_metrics(db))


@router.get("/audit-events")
def list_audit_events(db: Session = Depends(get_db)) -> dict[str, list[AuditEventRead]]:
    rows = db.execute(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(200)).scalars().all()
    return {"items": [AuditEventRead.model_validate(item, from_attributes=True) for item in rows]}
