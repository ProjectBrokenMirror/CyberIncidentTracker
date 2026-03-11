from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organization import Organization


def match_organization(record: dict, db: Session) -> dict:
    org_name = (record.get("organization_name") or "").strip()
    title = (record.get("title") or "").strip()

    if org_name:
        exact = db.execute(
            select(Organization).where(func.lower(Organization.canonical_name) == org_name.lower()).limit(1)
        ).scalars().first()
        if exact:
            record["matched_org_id"] = exact.id
            record["match_confidence"] = 0.9
            return record

    if title:
        title_lower = title.lower()
        candidates = db.execute(select(Organization).limit(500)).scalars().all()
        for org in candidates:
            if org.canonical_name.lower() in title_lower:
                record["matched_org_id"] = org.id
                record["match_confidence"] = 0.7
                return record

    record["matched_org_id"] = None
    record["match_confidence"] = 0.0
    return record
