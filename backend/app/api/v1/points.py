from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
from app.core.security import get_current_user
from app.modules.hw.gpio_mock import MockGpioDriver

router = APIRouter()


class Point(BaseModel):
    id: str
    value: float


# simple in-memory mock points
MOCK_POINTS = [Point(id="p1", value=1.23), Point(id="p2", value=4.56)]


@router.get("/", response_model=List[Point])
async def list_points(user: dict = Depends(get_current_user)):
    # Example: read from HW via driver interface (mocked here)
    driver = MockGpioDriver()
    _ = driver.read(1)
    return MOCK_POINTS
