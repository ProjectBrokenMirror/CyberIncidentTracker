from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorRead

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
