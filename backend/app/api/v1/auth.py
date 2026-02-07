from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.security import create_access_token, get_current_user

router = APIRouter()


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn):
    # Fake authentication for scaffold. Replace with real check.
    if payload.username == "admin" and payload.password == "ftqwertyu$01":
        token = create_access_token(subject=payload.username)
        return {"access_token": token}
    else:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user": user}
