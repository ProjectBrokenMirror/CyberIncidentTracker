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
