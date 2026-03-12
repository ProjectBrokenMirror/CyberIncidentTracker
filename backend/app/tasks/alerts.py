from datetime import datetime, timedelta, timezone
import smtplib

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.incident import Incident
from app.models.notification_event import NotificationEvent
from app.models.vendor import Vendor
from app.models.vendor_watcher import VendorWatcher


def _next_retry_time(attempt_count: int) -> datetime:
    # Exponential backoff: base, 2x, 4x...
    multiplier = max(1, 2 ** max(0, attempt_count - 1))
    delay_seconds = settings.alert_retry_backoff_seconds * multiplier
    return datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)


def _apply_send_result(
    event: NotificationEvent,
    ok: bool,
    error: str | None,
    *,
    increment_attempt: bool,
) -> tuple[bool, bool]:
    if increment_attempt:
        if event.attempt_count is None:
            event.attempt_count = 0
        event.attempt_count += 1
        event.last_attempt_at = datetime.now(timezone.utc)

    if ok:
        event.status = "sent"
        event.error_message = None
        event.sent_at = datetime.now(timezone.utc)
        event.next_retry_at = None
        return True, False

    if error == "email_alerts_disabled":
        event.status = "skipped_disabled"
        event.error_message = None
        event.next_retry_at = None
        return False, False

    event.error_message = error
    if event.attempt_count >= settings.alert_retry_max_attempts:
        event.status = "failed_exhausted"
        event.next_retry_at = None
        return False, True

    event.status = "failed"
    event.next_retry_at = _next_retry_time(event.attempt_count)
    return False, True


def send_email_alert(recipient_email: str, subject: str, body: str) -> tuple[bool, str | None]:
    if not settings.enable_email_alerts:
        return False, "email_alerts_disabled"

    message = (
        f"From: {settings.alerts_from_email}\r\n"
        f"To: {recipient_email}\r\n"
        f"Subject: {subject}\r\n"
        "\r\n"
        f"{body}\r\n"
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.sendmail(settings.alerts_from_email, [recipient_email], message)
        return True, None
    except Exception as exc:  # pragma: no cover - network/system-specific failure path
        return False, str(exc)


def dispatch_alerts_for_incident(
    db: Session,
    incident: Incident,
    source_name: str,
    source_url: str,
) -> dict[str, int]:
    vendors = db.execute(select(Vendor).where(Vendor.organization_id == incident.org_id)).scalars().all()
    if not vendors:
        return {"attempted": 0, "sent": 0, "failed": 0}

    attempted = 0
    sent = 0
    failed = 0

    for vendor in vendors:
        watchers = (
            db.execute(
                select(VendorWatcher).where(
                    VendorWatcher.vendor_id == vendor.id,
                    VendorWatcher.tenant_id == vendor.tenant_id,
                    VendorWatcher.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )
        for watcher in watchers:
            attempted += 1
            subject = f"[Incident Finder] New incident for vendor #{vendor.id}"
            body = (
                f"Organization ID: {incident.org_id}\n"
                f"Incident ID: {incident.id}\n"
                f"Type: {incident.incident_type}\n"
                f"Severity: {incident.severity}\n"
                f"Status: {incident.status}\n"
                f"Confidence: {incident.confidence}\n"
                f"Source: {source_name}\n"
                f"URL: {source_url}\n"
            )
            event = NotificationEvent(
                tenant_id=vendor.tenant_id,
                vendor_id=vendor.id,
                incident_id=incident.id,
                recipient_email=watcher.email,
                status="pending",
            )
            ok, error = send_email_alert(watcher.email, subject, body)
            did_send, did_fail = _apply_send_result(event, ok, error, increment_attempt=True)
            if did_send:
                sent += 1
            elif did_fail:
                failed += 1
            db.add(event)

    return {"attempted": attempted, "sent": sent, "failed": failed}


def retry_failed_alert_events(db: Session, batch_size: int = 100) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    retryable = (
        db.execute(
            select(NotificationEvent)
            .where(
                NotificationEvent.status == "failed",
                NotificationEvent.attempt_count < settings.alert_retry_max_attempts,
                or_(NotificationEvent.next_retry_at.is_(None), NotificationEvent.next_retry_at <= now),
            )
            .order_by(NotificationEvent.id.asc())
            .limit(batch_size)
        )
        .scalars()
        .all()
    )

    attempted = 0
    sent = 0
    failed = 0
    for event in retryable:
        attempted += 1
        subject = f"[Incident Finder] Retry alert for vendor #{event.vendor_id}"
        body = (
            f"Incident ID: {event.incident_id}\n"
            f"Vendor ID: {event.vendor_id}\n"
            "This is a retry notification after a prior send failure.\n"
        )
        ok, error = send_email_alert(event.recipient_email, subject, body)
        did_send, did_fail = _apply_send_result(event, ok, error, increment_attempt=True)
        if did_send:
            sent += 1
        elif did_fail:
            failed += 1
        db.add(event)

    if attempted:
        db.commit()

    return {"attempted": attempted, "sent": sent, "failed": failed}


def read_alert_metrics(db: Session) -> dict[str, int]:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    status_case_sent = case((NotificationEvent.status == "sent", 1), else_=0)
    status_case_failed = case((NotificationEvent.status.in_(["failed", "failed_exhausted"]), 1), else_=0)
    status_case_failed_exhausted = case((NotificationEvent.status == "failed_exhausted", 1), else_=0)
    status_case_skipped = case((NotificationEvent.status == "skipped_disabled", 1), else_=0)
    status_case_retryable = case((NotificationEvent.status == "failed", 1), else_=0)

    totals = db.execute(
        select(
            func.count(NotificationEvent.id),
            func.sum(status_case_sent),
            func.sum(status_case_failed),
            func.sum(status_case_failed_exhausted),
            func.sum(status_case_skipped),
            func.sum(status_case_retryable),
        )
    ).one()
    recent = db.execute(
        select(
            func.count(NotificationEvent.id),
            func.sum(status_case_sent),
            func.sum(status_case_failed),
            func.sum(status_case_skipped),
        ).where(NotificationEvent.created_at >= since)
    ).one()
    return {
        "total_events": int(totals[0] or 0),
        "sent_events": int(totals[1] or 0),
        "failed_events": int(totals[2] or 0),
        "failed_exhausted_events": int(totals[3] or 0),
        "skipped_events": int(totals[4] or 0),
        "retryable_failed_events": int(totals[5] or 0),
        "last_24h_total": int(recent[0] or 0),
        "last_24h_sent": int(recent[1] or 0),
        "last_24h_failed": int(recent[2] or 0),
        "last_24h_skipped": int(recent[3] or 0),
    }
