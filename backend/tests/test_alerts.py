from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.models.incident import Incident
from app.models.notification_event import NotificationEvent
from app.models.organization import Organization
from app.models.vendor import Vendor
from app.tasks.alerts import retry_failed_alert_events


def test_retry_failed_alert_events_marks_event_sent(monkeypatch, db_session) -> None:
    org = Organization(canonical_name="Retry Org", domain="retry.example")
    db_session.add(org)
    db_session.flush()
    incident = Incident(org_id=org.id, incident_type="data_breach", status="new", severity="high", confidence=0.9)
    db_session.add(incident)
    db_session.flush()
    vendor = Vendor(tenant_id="default", organization_id=org.id, owner="Risk Team", criticality="high")
    db_session.add(vendor)
    db_session.flush()
    event = NotificationEvent(
        tenant_id="default",
        vendor_id=vendor.id,
        incident_id=incident.id,
        recipient_email="alerts@example.com",
        status="failed",
        attempt_count=1,
        next_retry_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        error_message="temporary failure",
    )
    db_session.add(event)
    db_session.commit()

    monkeypatch.setattr("app.tasks.alerts.send_email_alert", lambda *_args, **_kwargs: (True, None))
    result = retry_failed_alert_events(db_session)
    assert result == {"attempted": 1, "sent": 1, "failed": 0}

    db_session.refresh(event)
    assert event.status == "sent"
    assert event.sent_at is not None
    assert event.attempt_count == 2
    assert event.next_retry_at is None


def test_retry_failed_alert_events_exhausts_after_max_attempts(monkeypatch, db_session) -> None:
    org = Organization(canonical_name="Retry Exhaust Org", domain="retry-exhaust.example")
    db_session.add(org)
    db_session.flush()
    incident = Incident(org_id=org.id, incident_type="data_breach", status="new", severity="high", confidence=0.9)
    db_session.add(incident)
    db_session.flush()
    vendor = Vendor(tenant_id="default", organization_id=org.id, owner="Risk Team", criticality="high")
    db_session.add(vendor)
    db_session.flush()
    event = NotificationEvent(
        tenant_id="default",
        vendor_id=vendor.id,
        incident_id=incident.id,
        recipient_email="alerts@example.com",
        status="failed",
        attempt_count=1,
        next_retry_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        error_message="temporary failure",
    )
    db_session.add(event)
    db_session.commit()

    previous_max_attempts = settings.alert_retry_max_attempts
    settings.alert_retry_max_attempts = 2
    try:
        monkeypatch.setattr("app.tasks.alerts.send_email_alert", lambda *_args, **_kwargs: (False, "still failing"))
        result = retry_failed_alert_events(db_session)
    finally:
        settings.alert_retry_max_attempts = previous_max_attempts

    assert result == {"attempted": 1, "sent": 0, "failed": 1}
    db_session.refresh(event)
    assert event.status == "failed_exhausted"
    assert event.attempt_count == 2
    assert event.next_retry_at is None
