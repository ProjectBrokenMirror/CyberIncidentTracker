from dataclasses import dataclass


@dataclass
class RawIncidentRecord:
    source_name: str
    source_url: str
    title: str
    published_at: str | None = None
    organization_name: str | None = None


class SourceConnector:
    source_name: str = "base"

    def fetch(self) -> list[RawIncidentRecord]:
        raise NotImplementedError
