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


class VendorImportRequest(BaseModel):
    organization_ids: list[int] | None = None
    owner: str | None = None
    criticality: str = "medium"
    only_with_incidents: bool = True
    limit: int = 100


class VendorImportResult(BaseModel):
    requested_count: int
    created_count: int
    skipped_existing_count: int
    created_vendor_ids: list[int]
