from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    canonical_name: str
    domain: str | None = None


class OrganizationRead(BaseModel):
    id: int
    canonical_name: str
    domain: str | None = None
