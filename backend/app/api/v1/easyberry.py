import os
import logging
from fastapi import APIRouter, HTTPException

from app.modules.sw.easyberry import auth as eb_auth
from app.modules.sw.easyberry import runner as eb_runner
from app.modules.sw.easyberry.config import read_config

router = APIRouter()
logger = logging.getLogger(__name__)


def _config_path():
    return os.path.join(os.getcwd(), "easyberry_config.json")


@router.post("/login")
async def login():
    path = _config_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="easyberry_config.json not found")
    # build URL and payload from config to include in error responses
    try:
        cfg = read_config(path)
        settings = cfg.get("settings", {})
        base = (settings.get("url") or "").rstrip("/")
        context = (settings.get("context") or "").strip("/")
        auth_path = settings.get("authPath") or "auth"
        if isinstance(auth_path, str) and auth_path.lower().startswith(('http://', 'https://')):
            url = auth_path
        else:
            url = "/".join([p for p in (base, context, auth_path) if p])
        payload = {"username": settings.get("username"), "password": settings.get("password")}
    except Exception:
        url = None
        payload = None

    try:
        token = eb_auth.login_and_persist_token(path)
        return {"ok": True, "token": bool(token)}
    except Exception as e:
        logger.exception("easyberry login failed")
        detail = {"error": str(e), "url": url, "payload": payload}
        raise HTTPException(status_code=500, detail=detail)


@router.post("/start")
async def start():
    try:
        ok = eb_runner.start()
        return {"started": bool(ok)}
    except Exception as e:
        logger.exception("failed to start easyberry runner")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop():
    try:
        ok = eb_runner.stop()
        return {"stopped": bool(ok)}
    except Exception as e:
        logger.exception("failed to stop easyberry runner")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def status():
    return eb_runner.status()
