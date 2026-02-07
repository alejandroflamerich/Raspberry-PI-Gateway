import os
import logging
from fastapi import APIRouter, HTTPException

from app.modules.sw.easyberry import auth as eb_auth
from app.modules.sw.easyberry import runner as eb_runner
from app.modules.sw.easyberry.config import read_config
from app.modules.sw.easyberry import connector as eb_connector

router = APIRouter()
logger = logging.getLogger(__name__)


def _config_path():
    # Ensure we read/write the config file from the backend folder so
    # the settings API and the easyberry endpoints operate on the same file.
    # backend/app/api/v1 -> parents[3] == backend
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    return str(root / 'easyberry_config.json')


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
        # attempt to return the raw response payload saved by auth
        try:
            from pathlib import Path
            root = Path(path).resolve().parent
            last_path = root / 'easyberry_last_auth.json'
            if last_path.exists():
                text = last_path.read_text(encoding='utf-8')
                try:
                    import json as _json
                    resp_payload = _json.loads(text)
                except Exception:
                    resp_payload = text
            else:
                resp_payload = None
        except Exception:
            resp_payload = None
        return {"ok": True, "token": token, "response": resp_payload}
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


@router.post("/send")
async def send_once():
    path = _config_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="easyberry_config.json not found")
    try:
        # import shared database and call send_once to post current database values
        from app.modules.sw.easyberry.store import database
        status_code, body = eb_connector.send_once(path, database)
        return {"status": int(status_code), "body": body}
    except Exception as e:
        logger.exception("easyberry send failed")
        raise HTTPException(status_code=500, detail=str(e))
