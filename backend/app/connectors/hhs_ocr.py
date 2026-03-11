import logging
from html import unescape
import re

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
        body_match = re.search(
            r'<tbody[^>]*id="ocrForm:reportResultTable_data"[^>]*>(.*?)</tbody>',
            html,
            re.DOTALL | re.IGNORECASE,
        )
        if not body_match:
            logger.warning("HHS OCR report table not found")
            return []

        tbody_html = body_match.group(1)
        rows = re.finditer(r"<tr\b([^>]*)>(.*?)</tr>", tbody_html, re.DOTALL | re.IGNORECASE)

        records: list[RawIncidentRecord] = []
        for idx, row_match in enumerate(rows):
            if idx >= settings.connector_max_records:
                break
            row_attrs = row_match.group(1) or ""
            row_html = row_match.group(2) or ""
            cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row_html, re.DOTALL | re.IGNORECASE)
            # Table columns include a leading row-toggler cell.
            if len(cells) < 8:
                continue
            org_name = self._clean_cell(cells[1])
            submission_date = self._clean_cell(cells[5]) or None
            breach_type = self._clean_cell(cells[6]) or "Breach"
            row_key_match = re.search(r'data-rk="([^"]+)"', row_attrs)
            row_key = row_key_match.group(1) if row_key_match else f"{idx}"

            if not org_name:
                continue

            records.append(
                RawIncidentRecord(
                    source_name=self.source_name,
                    source_url=f"{settings.hhs_ocr_report_url}#rk={row_key}",
                    title=f"{org_name}: {breach_type}",
                    published_at=submission_date,
                    organization_name=org_name,
                )
            )
        return records

    @staticmethod
    def _clean_cell(cell_html: str) -> str:
        text = re.sub(r"<[^>]+>", " ", cell_html)
        text = unescape(text)
        return re.sub(r"\s+", " ", text).strip()
