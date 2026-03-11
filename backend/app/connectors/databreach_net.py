import xml.etree.ElementTree as ET
import logging

import httpx

from app.connectors.base import RawIncidentRecord, SourceConnector
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataBreachesConnector(SourceConnector):
    source_name = "databreaches_net"

    def fetch(self) -> list[RawIncidentRecord]:
        try:
            response = httpx.get(
                settings.databreaches_feed_url,
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": settings.sec_user_agent},
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        body = response.text
        if "Just a moment..." in body or "__cf_chl_opt" in body:
            logger.warning("DataBreaches feed blocked by challenge page")
            return []

        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return []

        records: list[RawIncidentRecord] = []
        items = root.findall(".//item")
        for item in items[: settings.connector_max_records]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            published_at = (item.findtext("pubDate") or "").strip() or None
            if not title or not link:
                continue

            # Heuristic organization hint extraction from headline prefix.
            organization_name = title.split(":")[0].strip() if ":" in title else None
            records.append(
                RawIncidentRecord(
                    source_name=self.source_name,
                    source_url=link,
                    title=title,
                    published_at=published_at,
                    organization_name=organization_name,
                )
            )
        return records
