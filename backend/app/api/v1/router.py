from fastapi import APIRouter
from app.api.v1 import health, auth, points
from app.api.v1 import modbus, debug, settings
from app.api.v1 import easyberry

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(points.router, prefix="/points", tags=["points"])
api_router.include_router(modbus.router, prefix="/modbus", tags=["modbus"]) 
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(easyberry.router, prefix="/easyberry", tags=["easyberry"])
