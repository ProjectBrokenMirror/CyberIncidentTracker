import logging
import xml.etree.ElementTree as ET

import httpx

from app.connectors.base import RawIncidentRecord, SourceConnector
from app.core.config import settings

logger = logging.getLogger(__name__)


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

            # SEC title format often starts with company name before a dash.
            organization_name = title.split(" - ")[0].strip() if " - " in title else None
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
