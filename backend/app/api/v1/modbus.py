from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.modules.sw.modbus import default_store

router = APIRouter()


@router.get("/status")
async def modbus_status(user: dict = Depends(get_current_user)):
    """Return the current status of all pollers (in-memory)."""
    data = default_store.get_all()
    return data
