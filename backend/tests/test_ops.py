from datetime import datetime, timedelta, timezone

from app.models.ingestion_run import IngestionRun
from app.models.incident import Incident
from app.models.notification_event import NotificationEvent
from app.models.organization import Organization
from app.models.vendor import Vendor


def test_list_ingestion_runs_returns_recent_runs(client, db_session) -> None:
    db_session.add(
        IngestionRun(
            status="success",
            total_raw=10,
            total_normalized=10,
            total_deduped=9,
            total_persisted=8,
            total_unmatched=1,
            total_skipped_duplicates=1,
            total_organizations_created=2,
        )
    )
    db_session.commit()

    response = client.get("/api/v1/ops/ingestion-runs")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["status"] == "success"


def test_alert_metrics_endpoint_returns_counts(client, db_session) -> None:
    org = Organization(canonical_name="Ops Org", domain="ops.example")
    db_session.add(org)
    db_session.flush()
    incident_1 = Incident(org_id=org.id, incident_type="data_breach", status="new", severity="high", confidence=0.9)
    incident_2 = Incident(org_id=org.id, incident_type="data_breach", status="new", severity="high", confidence=0.9)
    incident_3 = Incident(org_id=org.id, incident_type="data_breach", status="new", severity="high", confidence=0.9)
    db_session.add_all([incident_1, incident_2, incident_3])
    db_session.flush()
    vendor = Vendor(tenant_id="default", organization_id=org.id, owner="Risk Team", criticality="high")
    db_session.add(vendor)
    db_session.flush()
    db_session.add_all(
        [
            NotificationEvent(
                tenant_id="default",
                vendor_id=vendor.id,
                incident_id=incident_1.id,
                recipient_email="sent@example.com",
                status="sent",
                sent_at=datetime.now(timezone.utc),
            ),
            NotificationEvent(
                tenant_id="default",
                vendor_id=vendor.id,
                incident_id=incident_2.id,
                recipient_email="failed@example.com",
                status="failed",
                error_message="smtp error",
            ),
            NotificationEvent(
                tenant_id="default",
                vendor_id=vendor.id,
                incident_id=incident_3.id,
                recipient_email="skipped@example.com",
                status="skipped_disabled",
                created_at=datetime.now(timezone.utc) - timedelta(days=2),
            ),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/ops/alerts/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_events"] == 3
    assert payload["sent_events"] == 1
    assert payload["failed_events"] == 1
    assert payload["failed_exhausted_events"] == 0
    assert payload["skipped_events"] == 1
    assert payload["retryable_failed_events"] == 1
    assert payload["last_24h_total"] == 2
