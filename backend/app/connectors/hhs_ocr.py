import logging

import httpx

from app.connectors.base import RawIncidentRecord, SourceConnector
from app.core.config import settings

logger = logging.getLogger(__name__)


class HhsOcrConnector(SourceConnector):
    source_name = "hhs_ocr"

    def fetch(self) -> list[RawIncidentRecord]:
        try:
            response = httpx.get(settings.hhs_ocr_api_url, timeout=20.0, follow_redirects=True)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            logger.warning("HHS OCR source request or decode failed")
            return []

        if not isinstance(payload, list):
            return []

        records: list[RawIncidentRecord] = []
        for item in payload[: settings.connector_max_records]:
            if not isinstance(item, dict):
                continue

            org_name = (
                item.get("name_of_covered_entity")
                or item.get("covered_entity_name")
                or item.get("organization_name")
                or ""
            ).strip()

            breach_type = (item.get("type_of_breach") or item.get("breach_type") or "Breach").strip()
            submission_date = (
                item.get("breach_submission_date")
                or item.get("submitted_date")
                or item.get("date_submitted")
                or item.get("created_at")
            )
            source_url = "https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf"

            if not org_name:
                continue

            title = f"{org_name}: {breach_type}"
            records.append(
                RawIncidentRecord(
                    source_name=self.source_name,
                    source_url=source_url,
                    title=title,
                    published_at=str(submission_date) if submission_date else None,
                    organization_name=org_name,
                )
            )
        return records
