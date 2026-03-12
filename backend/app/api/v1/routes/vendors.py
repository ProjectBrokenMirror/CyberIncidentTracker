from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import AuthContext, get_auth_context
from app.models.incident import Incident
from app.models.organization import Organization
from app.models.vendor import Vendor
from app.models.vendor_watcher import VendorWatcher
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
    db.commit()
    db.refresh(watcher)
    return VendorWatcherRead.model_validate(watcher, from_attributes=True)
