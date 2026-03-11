from app.connectors.base import RawIncidentRecord, SourceConnector
from app.models.incident import Incident
from app.models.incident_source import IncidentSource
from app.models.organization import Organization
from app.tasks.ingestion import run_wave1_ingestion


class FakeConnector(SourceConnector):
    source_name = "databreaches_net"

    def fetch(self) -> list[RawIncidentRecord]:
        return [
            RawIncidentRecord(
                source_name=self.source_name,
                source_url="https://example.com/advisory/acme-incident",
                title="Acme Corp: Breach Reported",
                organization_name="Acme Corp",
            )
        ]


def test_run_wave1_ingestion_persists_incidents(monkeypatch, db_session) -> None:
    db_session.add(Organization(canonical_name="Acme Corp", domain="acme.example"))
    db_session.commit()

    monkeypatch.setattr("app.tasks.ingestion.wave1_connectors", lambda: [FakeConnector()])

    result = run_wave1_ingestion(db=db_session)
    assert result["total_raw"] == 1
    assert result["total_persisted"] == 1
    assert result["total_unmatched"] == 0

    incidents = db_session.query(Incident).all()
    sources = db_session.query(IncidentSource).all()
    assert len(incidents) == 1
    assert len(sources) == 1


def test_run_wave1_ingestion_skips_duplicate_sources(monkeypatch, db_session) -> None:
    db_session.add(Organization(canonical_name="Acme Corp", domain="acme.example"))
    db_session.commit()

    monkeypatch.setattr("app.tasks.ingestion.wave1_connectors", lambda: [FakeConnector()])

    first = run_wave1_ingestion(db=db_session)
    second = run_wave1_ingestion(db=db_session)

    assert first["total_persisted"] == 1
    assert second["total_skipped_duplicates"] == 1

    incidents = db_session.query(Incident).all()
    sources = db_session.query(IncidentSource).all()
    assert len(incidents) == 1
    assert len(sources) == 1
