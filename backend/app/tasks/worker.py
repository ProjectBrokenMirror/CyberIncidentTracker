from celery import Celery

from app.core.config import settings
from app.core.database import SessionLocal
from app.tasks.alerts import retry_failed_alert_events
from app.tasks.ingestion import run_wave1_ingestion

celery_app = Celery("incident_tracker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.beat_schedule = {
    "ingest-wave1-hourly": {
        "task": "app.tasks.worker.ingest_wave1_sources",
        "schedule": 3600.0,
    },
    "retry-failed-alerts-every-5m": {
        "task": "app.tasks.worker.retry_failed_alerts",
        "schedule": 300.0,
    },
}
celery_app.conf.timezone = "UTC"


@celery_app.task
def ingest_wave1_sources() -> dict[str, int]:
    return run_wave1_ingestion()


@celery_app.task
def retry_failed_alerts() -> dict[str, int]:
    db = SessionLocal()
    try:
        return retry_failed_alert_events(db=db)
    finally:
        db.close()
