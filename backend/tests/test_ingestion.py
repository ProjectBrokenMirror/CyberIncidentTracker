from app.connectors.base import RawIncidentRecord, SourceConnector
from app.models.incident import Incident
from app.models.ingestion_run import IngestionRun
from app.models.incident_source import IncidentSource
from app.models.notification_event import NotificationEvent
from app.models.organization import Organization
from app.models.vendor import Vendor
from app.models.vendor_watcher import VendorWatcher
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


class FakeTrustedConnector(SourceConnector):
    source_name = "sec_edgar_8k"

    def fetch(self) -> list[RawIncidentRecord]:
        return [
            RawIncidentRecord(
                source_name=self.source_name,
                source_url="https://www.sec.gov/Archives/example-8k.htm",
                title="8-K - NewCo Inc - Current report filing",
                organization_name="NewCo Inc",
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
    runs = db_session.query(IngestionRun).all()
    assert len(incidents) == 1
    assert len(sources) == 1
    assert len(runs) == 1


def test_run_wave1_ingestion_auto_creates_org_for_trusted_source(monkeypatch, db_session) -> None:
    monkeypatch.setattr("app.tasks.ingestion.wave1_connectors", lambda: [FakeTrustedConnector()])

    result = run_wave1_ingestion(db=db_session)
    assert result["total_raw"] == 1
    assert result["total_organizations_created"] == 1
    assert result["total_persisted"] == 1
    assert result["total_unmatched"] == 0

    orgs = db_session.query(Organization).all()
    incidents = db_session.query(Incident).all()
    runs = db_session.query(IngestionRun).all()
    assert len(orgs) == 1
    assert orgs[0].canonical_name == "NewCo Inc"
    assert len(incidents) == 1
    assert len(runs) == 1


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
    runs = db_session.query(IngestionRun).all()
    assert len(incidents) == 1
    assert len(sources) == 1
    assert len(runs) == 2


def test_run_wave1_ingestion_dispatches_watcher_alerts(monkeypatch, db_session) -> None:
    org = Organization(canonical_name="Acme Corp", domain="acme.example")
    db_session.add(org)
    db_session.flush()
    vendor = Vendor(tenant_id="tenant-a", organization_id=org.id, owner="Risk Team", criticality="high")
    db_session.add(vendor)
    db_session.flush()
    watcher = VendorWatcher(tenant_id="tenant-a", vendor_id=vendor.id, email="risk@example.com", is_active=True)
    db_session.add(watcher)
    db_session.commit()

    monkeypatch.setattr("app.tasks.ingestion.wave1_connectors", lambda: [FakeConnector()])
    monkeypatch.setattr("app.tasks.alerts.send_email_alert", lambda *_args, **_kwargs: (True, None))

    result = run_wave1_ingestion(db=db_session)
    assert result["total_persisted"] == 1
    assert result["total_alerts_attempted"] == 1
    assert result["total_alerts_sent"] == 1
    assert result["total_alerts_failed"] == 0

    events = db_session.query(NotificationEvent).all()
    runs = db_session.query(IngestionRun).all()
    assert len(events) == 1
    assert events[0].status == "sent"
    assert runs[-1].total_alerts_sent == 1
