import logging
import re
import xml.etree.ElementTree as ET

import httpx

from app.connectors.base import RawIncidentRecord, SourceConnector
from app.core.config import settings

logger = logging.getLogger(__name__)
SEC_FORM_TYPES = {"8-K", "8K", "8-K/A", "6-K", "10-K", "10-Q"}


class Sec8KConnector(SourceConnector):
    source_name = "sec_edgar_8k"

    def fetch(self) -> list[RawIncidentRecord]:
        try:
            response = httpx.get(
                settings.sec_8k_feed_url,
                timeout=20.0,
                follow_redirects=True,
                headers={"User-Agent": settings.sec_user_agent},
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("SEC 8-K feed request failed")
            return []

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            logger.warning("SEC 8-K feed XML parsing failed")
            return []

        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall(".//atom:entry", namespace)
        records: list[RawIncidentRecord] = []
        for entry in entries[: settings.connector_max_records]:
            title = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
            published_at = (entry.findtext("atom:updated", default="", namespaces=namespace) or "").strip() or None
            link_element = entry.find("atom:link", namespace)
            source_url = ""
            if link_element is not None:
                source_url = (link_element.attrib.get("href") or "").strip()

            if not title or not source_url:
                continue

            organization_name = self._extract_org_name(title)
            records.append(
                RawIncidentRecord(
                    source_name=self.source_name,
                    source_url=source_url,
                    title=title,
                    published_at=published_at,
                    organization_name=organization_name,
                )
            )
        return records

    @staticmethod
    def _extract_org_name(title: str) -> str | None:
        parts = [part.strip() for part in title.split(" - ") if part.strip()]
        if not parts:
            return None
        if len(parts) == 1:
            return None if parts[0].upper() in SEC_FORM_TYPES else parts[0]

        left, right = parts[0], parts[1]
        if left.upper() in SEC_FORM_TYPES:
            return Sec8KConnector._normalize_org_name(right)
        if right.upper() in SEC_FORM_TYPES:
            return Sec8KConnector._normalize_org_name(left)
        return Sec8KConnector._normalize_org_name(left)

    @staticmethod
    def _normalize_org_name(name: str | None) -> str | None:
        if not name:
            return None
        normalized = re.sub(r"\s+\(\d{6,}\)\s+\(Filer\)$", "", name).strip()
        normalized = re.sub(r"\s+\(Filer\)$", "", normalized).strip()
        return normalized or None
