from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationRead

router = APIRouter()


@router.get("/")
def list_organizations(db: Session = Depends(get_db)) -> dict[str, list[OrganizationRead]]:
    items = db.execute(select(Organization).order_by(Organization.id.desc()).limit(100)).scalars().all()
    return {"items": [OrganizationRead.model_validate(item, from_attributes=True) for item in items]}


@router.post("/", response_model=OrganizationRead)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)) -> OrganizationRead:
    org = Organization(canonical_name=payload.canonical_name, domain=payload.domain)
    db.add(org)
    db.commit()
    db.refresh(org)
    return OrganizationRead.model_validate(org, from_attributes=True)


@router.get("/{organization_id}/timeline")
def get_organization_timeline(organization_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"organization_id": organization_id, "events": []}
