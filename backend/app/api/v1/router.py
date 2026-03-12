from fastapi import APIRouter, Depends

from app.api.v1.routes import incidents, ops, organizations, vendors
from app.core.auth import require_api_key

api_router = APIRouter(dependencies=[Depends(require_api_key)])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
api_router.include_router(ops.router, prefix="/ops", tags=["ops"])
