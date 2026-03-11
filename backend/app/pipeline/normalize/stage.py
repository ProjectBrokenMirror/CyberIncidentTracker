from app.connectors.base import RawIncidentRecord


def normalize_records(records: list[RawIncidentRecord]) -> list[dict]:
    normalized: list[dict] = []
    for record in records:
        normalized.append(
            {
                "source_name": record.source_name,
                "source_url": record.source_url,
                "title": record.title.strip(),
                "published_at": record.published_at,
                "organization_name": record.organization_name,
            }
        )
    return normalized
