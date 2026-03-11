from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ingestion_run import IngestionRun
from app.schemas.ingestion import IngestionRunRead

router = APIRouter()


@router.get("/ingestion-runs")
def list_ingestion_runs(db: Session = Depends(get_db)) -> dict[str, list[IngestionRunRead]]:
    runs = db.execute(select(IngestionRun).order_by(IngestionRun.id.desc()).limit(50)).scalars().all()
    return {"items": [IngestionRunRead.model_validate(run, from_attributes=True) for run in runs]}
