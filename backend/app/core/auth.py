from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.core.config import settings


@dataclass
class AuthContext:
    tenant_id: str


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if not settings.require_api_key:
        return
    valid_keys = {key.strip() for key in settings.api_keys.split(",") if key.strip()}
    if not x_api_key or x_api_key not in valid_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def get_auth_context(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")) -> AuthContext:
    tenant_id = (x_tenant_id or settings.default_tenant_id).strip() or settings.default_tenant_id
    return AuthContext(tenant_id=tenant_id)
