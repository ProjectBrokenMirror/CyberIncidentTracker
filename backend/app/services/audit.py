from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def log_audit_event(
    db: Session,
    *,
    tenant_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict[str, object] | None = None,
) -> None:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details or {}, sort_keys=True),
    )
    db.add(event)
