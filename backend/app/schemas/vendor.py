from pydantic import BaseModel


class VendorCreate(BaseModel):
    organization_id: int
    owner: str | None = None
    criticality: str = "medium"


class VendorRead(BaseModel):
    id: int
    organization_id: int
    owner: str | None = None
    criticality: str


class VendorSummaryRead(BaseModel):
    vendor_id: int
    organization_id: int
    organization_name: str
    criticality: str
    total_incidents: int
    new_incidents: int
    resolved_incidents: int
