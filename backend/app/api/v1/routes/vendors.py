import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import AuthContext, get_auth_context, require_manager_role
from app.models.incident import Incident
from app.models.notification_event import NotificationEvent
from app.models.organization import Organization
from app.models.vendor import Vendor
from app.models.vendor_watcher import VendorWatcher
from app.services.audit import log_audit_event
from app.schemas.alerts import VendorWatcherCreate, VendorWatcherRead
from app.schemas.incident import IncidentRead
from app.schemas.vendor import VendorCreate, VendorImportRequest, VendorImportResult, VendorRead, VendorSummaryRead

router = APIRouter()


@router.get("/")
def list_vendors(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, list[VendorRead]]:
    items = (
        db.execute(select(Vendor).where(Vendor.tenant_id == auth.tenant_id).order_by(Vendor.id.desc()).limit(100))
        .scalars()
        .all()
    )
    return {"items": [VendorRead.model_validate(item, from_attributes=True) for item in items]}


@router.post("/", response_model=VendorRead)
def create_vendor(
    payload: VendorCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> VendorRead:
    vendor = Vendor(
        tenant_id=auth.tenant_id,
        organization_id=payload.organization_id,
        owner=payload.owner,
        criticality=payload.criticality,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return VendorRead.model_validate(vendor, from_attributes=True)


@router.post("/import", response_model=VendorImportResult)
def import_vendors(
    payload: VendorImportRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> VendorImportResult:
    org_query = select(Organization.id)
    if payload.organization_ids:
        org_query = org_query.where(Organization.id.in_(payload.organization_ids))

    if payload.only_with_incidents:
        org_query = org_query.join(Incident, Incident.org_id == Organization.id).group_by(Organization.id)

    org_ids = [row[0] for row in db.execute(org_query.order_by(Organization.id.desc()).limit(payload.limit)).all()]
    if not org_ids:
        return VendorImportResult(
            requested_count=0,
            created_count=0,
            skipped_existing_count=0,
            created_vendor_ids=[],
        )

    existing_vendor_org_ids = {
        row[0]
        for row in db.execute(
            select(Vendor.organization_id).where(
                Vendor.organization_id.in_(org_ids), Vendor.tenant_id == auth.tenant_id
            )
        ).all()
    }

    created_vendor_ids: list[int] = []
    skipped_existing_count = 0
    for org_id in org_ids:
        if org_id in existing_vendor_org_ids:
            skipped_existing_count += 1
            continue
        vendor = Vendor(
            tenant_id=auth.tenant_id,
            organization_id=org_id,
            owner=payload.owner,
            criticality=payload.criticality,
        )
        db.add(vendor)
        db.flush()
        created_vendor_ids.append(vendor.id)

    db.commit()
    return VendorImportResult(
        requested_count=len(org_ids),
        created_count=len(created_vendor_ids),
        skipped_existing_count=skipped_existing_count,
        created_vendor_ids=created_vendor_ids,
    )


@router.get("/summary")
def list_vendor_summary(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, list[VendorSummaryRead]]:
    rows = db.execute(
        select(
            Vendor.id.label("vendor_id"),
            Vendor.organization_id.label("organization_id"),
            Organization.canonical_name.label("organization_name"),
            Vendor.criticality.label("criticality"),
            func.count(Incident.id).label("total_incidents"),
            func.sum(case((Incident.status == "new", 1), else_=0)).label("new_incidents"),
            func.sum(case((Incident.status == "resolved", 1), else_=0)).label("resolved_incidents"),
        )
        .join(Organization, Organization.id == Vendor.organization_id)
        .outerjoin(Incident, Incident.org_id == Vendor.organization_id)
        .where(Vendor.tenant_id == auth.tenant_id)
        .group_by(Vendor.id, Vendor.organization_id, Organization.canonical_name, Vendor.criticality)
        .order_by(Vendor.id.desc())
        .limit(200)
    ).all()

    items = [
        VendorSummaryRead(
            vendor_id=row.vendor_id,
            organization_id=row.organization_id,
            organization_name=row.organization_name,
            criticality=row.criticality,
            total_incidents=int(row.total_incidents or 0),
            new_incidents=int(row.new_incidents or 0),
            resolved_incidents=int(row.resolved_incidents or 0),
        )
        for row in rows
    ]
    return {"items": items}


@router.get("/{vendor_id}/incidents")
def get_vendor_incidents(
    vendor_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, object]:
    vendor = db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.tenant_id == auth.tenant_id)
    ).scalar_one_or_none()
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")

    organization_name = db.execute(
        select(Organization.canonical_name).where(Organization.id == vendor.organization_id)
    ).scalar_one_or_none()

    incidents = (
        db.execute(
            select(Incident)
            .where(Incident.org_id == vendor.organization_id)
            .order_by(Incident.first_seen_at.desc(), Incident.id.desc())
            .limit(200)
        )
        .scalars()
        .all()
    )

    return {
        "vendor_id": vendor.id,
        "organization_id": vendor.organization_id,
        "organization_name": organization_name,
        "items": [IncidentRead.model_validate(item, from_attributes=True) for item in incidents],
    }


@router.get("/{vendor_id}/watchers")
def list_vendor_watchers(
    vendor_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, list[VendorWatcherRead]]:
    vendor = db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.tenant_id == auth.tenant_id)
    ).scalar_one_or_none()
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")

    watchers = (
        db.execute(
            select(VendorWatcher)
            .where(VendorWatcher.vendor_id == vendor_id, VendorWatcher.tenant_id == auth.tenant_id)
            .order_by(VendorWatcher.id.desc())
            .limit(200)
        )
        .scalars()
        .all()
    )
    return {"items": [VendorWatcherRead.model_validate(item, from_attributes=True) for item in watchers]}


@router.post("/{vendor_id}/watchers", response_model=VendorWatcherRead)
def create_vendor_watcher(
    vendor_id: int,
    payload: VendorWatcherCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    _manager: None = Depends(require_manager_role),
) -> VendorWatcherRead:
    vendor = db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.tenant_id == auth.tenant_id)
    ).scalar_one_or_none()
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")

    existing = db.execute(
        select(VendorWatcher).where(
            VendorWatcher.vendor_id == vendor_id,
            VendorWatcher.tenant_id == auth.tenant_id,
            VendorWatcher.email == payload.email,
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.is_active = payload.is_active
        db.add(existing)
        log_audit_event(
            db,
            tenant_id=auth.tenant_id,
            actor_role=auth.role,
            action="watcher_updated",
            resource_type="vendor_watcher",
            resource_id=str(existing.id),
            details={"vendor_id": vendor_id, "email": existing.email, "is_active": existing.is_active},
        )
        db.commit()
        db.refresh(existing)
        return VendorWatcherRead.model_validate(existing, from_attributes=True)

    watcher = VendorWatcher(
        tenant_id=auth.tenant_id,
        vendor_id=vendor_id,
        email=payload.email,
        is_active=payload.is_active,
    )
    db.add(watcher)
    db.flush()
    log_audit_event(
        db,
        tenant_id=auth.tenant_id,
        actor_role=auth.role,
        action="watcher_created",
        resource_type="vendor_watcher",
        resource_id=str(watcher.id),
        details={"vendor_id": vendor_id, "email": watcher.email, "is_active": watcher.is_active},
    )
    db.commit()
    db.refresh(watcher)
    return VendorWatcherRead.model_validate(watcher, from_attributes=True)


@router.delete("/{vendor_id}/watchers/{watcher_id}", response_model=VendorWatcherRead)
def deactivate_vendor_watcher(
    vendor_id: int,
    watcher_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    _manager: None = Depends(require_manager_role),
) -> VendorWatcherRead:
    vendor = db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.tenant_id == auth.tenant_id)
    ).scalar_one_or_none()
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")

    watcher = db.execute(
        select(VendorWatcher).where(
            VendorWatcher.id == watcher_id,
            VendorWatcher.vendor_id == vendor_id,
            VendorWatcher.tenant_id == auth.tenant_id,
        )
    ).scalar_one_or_none()
    if watcher is None:
        raise HTTPException(status_code=404, detail="Watcher not found")

    watcher.is_active = False
    db.add(watcher)
    log_audit_event(
        db,
        tenant_id=auth.tenant_id,
        actor_role=auth.role,
        action="watcher_deactivated",
        resource_type="vendor_watcher",
        resource_id=str(watcher.id),
        details={"vendor_id": vendor_id, "email": watcher.email, "is_active": watcher.is_active},
    )
    db.commit()
    db.refresh(watcher)
    return VendorWatcherRead.model_validate(watcher, from_attributes=True)


@router.get("/{vendor_id}/incidents.csv")
def export_vendor_incidents_csv(
    vendor_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> Response:
    vendor = db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.tenant_id == auth.tenant_id)
    ).scalar_one_or_none()
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")

    incidents = (
        db.execute(
            select(Incident)
            .where(Incident.org_id == vendor.organization_id)
            .order_by(Incident.first_seen_at.desc(), Incident.id.desc())
            .limit(5000)
        )
        .scalars()
        .all()
    )
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["incident_id", "org_id", "incident_type", "status", "severity", "confidence", "first_seen_at"])
    for item in incidents:
        writer.writerow([item.id, item.org_id, item.incident_type, item.status, item.severity, item.confidence, item.first_seen_at])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="vendor-{vendor_id}-incidents.csv"'},
    )


@router.get("/{vendor_id}/alerts.csv")
def export_vendor_alerts_csv(
    vendor_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> Response:
    vendor = db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.tenant_id == auth.tenant_id)
    ).scalar_one_or_none()
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")

    events = (
        db.execute(
            select(NotificationEvent)
            .where(NotificationEvent.vendor_id == vendor_id, NotificationEvent.tenant_id == auth.tenant_id)
            .order_by(NotificationEvent.id.desc())
            .limit(5000)
        )
        .scalars()
        .all()
    )
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "event_id",
            "incident_id",
            "recipient_email",
            "status",
            "attempt_count",
            "error_message",
            "created_at",
            "sent_at",
        ]
    )
    for item in events:
        writer.writerow(
            [
                item.id,
                item.incident_id,
                item.recipient_email,
                item.status,
                item.attempt_count,
                item.error_message or "",
                item.created_at,
                item.sent_at or "",
            ]
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="vendor-{vendor_id}-alerts.csv"'},
    )
