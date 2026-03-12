from datetime import datetime

from pydantic import BaseModel


class AuditEventRead(BaseModel):
    id: int
    tenant_id: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str | None
    details: str | None
    created_at: datetime
