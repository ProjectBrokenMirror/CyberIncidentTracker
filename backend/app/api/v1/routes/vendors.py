from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.incident import Incident
from app.models.organization import Organization
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorRead, VendorSummaryRead

router = APIRouter()


@router.get("/")
def list_vendors(db: Session = Depends(get_db)) -> dict[str, list[VendorRead]]:
    items = db.execute(select(Vendor).order_by(Vendor.id.desc()).limit(100)).scalars().all()
    return {"items": [VendorRead.model_validate(item, from_attributes=True) for item in items]}


@router.post("/", response_model=VendorRead)
def create_vendor(payload: VendorCreate, db: Session = Depends(get_db)) -> VendorRead:
    vendor = Vendor(
        organization_id=payload.organization_id,
        owner=payload.owner,
        criticality=payload.criticality,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return VendorRead.model_validate(vendor, from_attributes=True)


@router.post("/import")
def import_vendors() -> dict[str, str]:
    return {"status": "not_implemented"}


@router.get("/summary")
def list_vendor_summary(db: Session = Depends(get_db)) -> dict[str, list[VendorSummaryRead]]:
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
