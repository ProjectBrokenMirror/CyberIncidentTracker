from celery import Celery

from app.core.config import settings
from app.tasks.ingestion import run_wave1_ingestion

celery_app = Celery("incident_tracker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.beat_schedule = {
    "ingest-wave1-hourly": {
        "task": "app.tasks.worker.ingest_wave1_sources",
        "schedule": 3600.0,
    }
}
celery_app.conf.timezone = "UTC"


@celery_app.task
def ingest_wave1_sources() -> dict[str, int]:
    return run_wave1_ingestion()
