from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.security import create_access_token, get_current_user
from app.modules import crypto
from fastapi import HTTPException, status
from pathlib import Path
import shutil

router = APIRouter()


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn):
    # Use encrypted password file if present. On first login (no encrypted file)
    # create it using the provided password (first-time setup).
    if payload.username != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    # if encrypted password exists, compare
    if crypto.has_encrypted_password():
        stored = crypto.decrypt_password()
        if stored is None or stored != payload.password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")
        token = create_access_token(subject=payload.username)
        return {"access_token": token}
    else:
        # first time: create encrypted password file and accept login
        try:
            crypto.encrypt_password(payload.password)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to initialize credentials")
        token = create_access_token(subject=payload.username)
        return {"access_token": token}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user": user}


@router.post("/forgot")
async def forgot_password():
    """Reset easyberry config to example and remove stored encrypted credentials.
    This endpoint should be protected or rate limited in production.
    """
    try:
        backend_root = Path(__file__).resolve().parents[2]
        example = backend_root / 'easyberry_config.example.json'
        target = backend_root / 'easyberry_config.json'
        if example.exists():
            shutil.copy(example, target)
        # remove encrypted credentials
        crypto.delete_encrypted_password()
        return {"ok": True}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to reset configuration")
