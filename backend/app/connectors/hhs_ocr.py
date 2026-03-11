import logging
import re
import xml.etree.ElementTree as ET

import httpx

from app.connectors.base import RawIncidentRecord, SourceConnector
from app.core.config import settings

logger = logging.getLogger(__name__)


class HhsOcrConnector(SourceConnector):
    source_name = "hhs_ocr"

    def fetch(self) -> list[RawIncidentRecord]:
        try:
            with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                frontpage = client.get(settings.hhs_ocr_frontpage_url)
                frontpage.raise_for_status()
                view_state = self._extract_view_state(frontpage.text)
                if not view_state:
                    logger.warning("HHS OCR frontpage view state not found")
                    return []

                payload = {
                    "ocrForm": "ocrForm",
                    "ocrForm:j_idt39": "ocrForm:j_idt39",
                    "javax.faces.ViewState": view_state,
                }
                report = client.post(settings.hhs_ocr_frontpage_url, data=payload)
                report.raise_for_status()
        except httpx.HTTPError:
            logger.warning("HHS OCR source request failed")
            return []

        return self._parse_report_rows(report.text)

    @staticmethod
    def _extract_view_state(html: str) -> str | None:
        match = re.search(r'name="javax.faces.ViewState"[^>]*value="([^"]+)"', html)
        return match.group(1) if match else None

    def _parse_report_rows(self, html: str) -> list[RawIncidentRecord]:
        try:
            root = ET.fromstring(html)
        except ET.ParseError:
            logger.warning("HHS OCR report page parsing failed")
            return []

        table_body = root.find(".//*[@id='ocrForm:reportResultTable_data']")
        if table_body is None:
            logger.warning("HHS OCR report table not found")
            return []

        records: list[RawIncidentRecord] = []
        for row in table_body.findall("tr")[: settings.connector_max_records]:
            cells = row.findall("td")
            # Table columns include a leading row-toggler cell.
            if len(cells) < 8:
                continue
            org_name = "".join(cells[1].itertext()).strip()
            submission_date = "".join(cells[5].itertext()).strip() or None
            breach_type = "".join(cells[6].itertext()).strip() or "Breach"

            if not org_name:
                continue

            records.append(
                RawIncidentRecord(
                    source_name=self.source_name,
                    source_url=settings.hhs_ocr_report_url,
                    title=f"{org_name}: {breach_type}",
                    published_at=submission_date,
                    organization_name=org_name,
                )
            )
        return records
