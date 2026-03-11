from fastapi import APIRouter

from app.api.v1.routes import incidents, organizations, vendors

api_router = APIRouter()
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
