from datetime import datetime

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.connectors.registry import wave1_connectors
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.incident import Incident
from app.models.incident_source import IncidentSource
from app.models.organization import Organization
from app.pipeline.confidence import score_confidence
from app.pipeline.dedup import deduplicate
from app.pipeline.entity_match import match_organization
from app.pipeline.normalize import normalize_records


def _parse_published_at(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    try:
        return datetime.strptime(normalized, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        try:
            return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return None


def run_wave1_ingestion(db: Session | None = None) -> dict[str, int]:
    total_raw = 0
    total_normalized = 0
    total_deduped = 0
    total_persisted = 0
    total_unmatched = 0
    total_skipped_duplicates = 0
    total_organizations_created = 0
    auto_create_sources = {
        source.strip()
        for source in settings.auto_create_org_sources.split(",")
        if source.strip()
    }

    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    assert db is not None

    try:
        for connector in wave1_connectors():
            records = connector.fetch()
            total_raw += len(records)
            normalized = normalize_records(records)
            total_normalized += len(normalized)
            deduped = deduplicate(normalized)
            total_deduped += len(deduped)

            for item in deduped:
                source_name = item.get("source_name", "unknown")
                source_url = item.get("source_url", "")
                if not source_url:
                    total_unmatched += 1
                    continue

                duplicate_exists = db.execute(
                    select(exists().where(IncidentSource.source_name == source_name).where(IncidentSource.source_url == source_url))
                ).scalar_one()
                if duplicate_exists:
                    total_skipped_duplicates += 1
                    continue

                matched = match_organization(item, db)
                scored = score_confidence(matched)
                org_id = scored.get("matched_org_id")
                if not org_id and source_name in auto_create_sources:
                    org_name = (scored.get("organization_name") or "").strip()
                    if org_name:
                        existing_org = db.execute(
                            select(Organization).where(func.lower(Organization.canonical_name) == org_name.lower()).limit(1)
                        ).scalars().first()
                        if existing_org:
                            org_id = existing_org.id
                        else:
                            new_org = Organization(canonical_name=org_name, domain=None)
                            db.add(new_org)
                            db.flush()
                            org_id = new_org.id
                            total_organizations_created += 1

                if not org_id:
                    total_unmatched += 1
                    continue

                incident = Incident(
                    org_id=org_id,
                    incident_type="data_breach",
                    status="new",
                    severity="medium",
                    confidence=scored.get("confidence", 0.6),
                )
                db.add(incident)
                db.flush()
                db.add(
                    IncidentSource(
                        incident_id=incident.id,
                        source_name=source_name,
                        source_url=source_url,
                        published_at=_parse_published_at(scored.get("published_at")),
                    )
                )
                total_persisted += 1
        db.commit()
    finally:
        if owns_session:
            db.close()

    return {
        "total_raw": total_raw,
        "total_normalized": total_normalized,
        "total_deduped": total_deduped,
        "total_persisted": total_persisted,
        "total_unmatched": total_unmatched,
        "total_skipped_duplicates": total_skipped_duplicates,
        "total_organizations_created": total_organizations_created,
    }
