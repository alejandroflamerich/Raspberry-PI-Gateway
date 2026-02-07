from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from app.core.settings import settings

_security = HTTPBearer()


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    payload = {
        "sub": subject,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algo)
    return token


def decode_token(token: str) -> Optional[dict]:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algo])
        return data
    except jwt.PyJWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_security)) -> dict:
    token = credentials.credentials
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return {"sub": data.get("sub")}
