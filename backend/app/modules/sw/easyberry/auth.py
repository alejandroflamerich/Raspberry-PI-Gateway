import logging
import time
import json
from typing import Dict, Any, Optional

import httpx

from .config import read_config, write_config
from .packet_store import eb_packet_store

logger = logging.getLogger(__name__)


def _discover_token(resp_json: Dict[str, Any]) -> Optional[str]:
    # support common token fields
    for k in ("token", "access_token", "jwt", "accessToken"):
        if k in resp_json and resp_json[k]:
            return str(resp_json[k])
    return None


def login_and_persist_token(config_path: str) -> str:
    cfg = read_config(config_path)
    settings = cfg.get("settings", {})
    auth_path = settings.get("authPath", "auth")
    base = settings.get("url", "").rstrip("/")
    context = settings.get("context", "").strip("/")
    # If auth_path is an absolute URL, use it as-is. Otherwise build from base/context/auth_path
    if isinstance(auth_path, str) and auth_path.lower().startswith(('http://', 'https://')):
        url = auth_path
    else:
        parts = [p for p in (base, context, auth_path) if p]
        url = "/".join(parts)

    username = settings.get("username")
    password = settings.get("password")
    if not username or not password:
        raise ValueError("missing username/password in settings")

    logger.info("Easyberry: requesting token from %s", url)
    payload = {"username": username, "password": password}
    # Mask password for logs
    masked = {"username": username, "password": "***"}
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    try:
        logger.info("%s - LOGIN_REQUEST - url=%s - payload=%s", ts, url, json.dumps(masked, ensure_ascii=False))
        with httpx.Client(timeout=10.0) as client:
            # send username/password as JSON per spec
            r = client.post(url, json=payload)
        # record the raw response so frontend can inspect it even if token is missing
        try:
            eb_packet_store.add(url, json.dumps(payload, ensure_ascii=False), r.text, status=r.status_code, note='auth raw')
            try:
                with eb_packet_store._lock:
                    if len(eb_packet_store._deque) > 0:
                        eb_packet_store._deque[-1]['content_type'] = r.headers.get('content-type')
            except Exception:
                pass
        except Exception:
            pass
    except Exception as e:
        logger.exception("Easyberry login failed: %s", e)
        # record failed auth attempt in easyberry packet store
        try:
            eb_packet_store.add(url, json.dumps(payload, ensure_ascii=False), None, status=None, note=str(e))
        except Exception:
            pass
        raise

    if r.status_code != 200:
        logger.error("Easyberry login failed status=%s body=%s", r.status_code, r.text[:200])
        # record response in packet store for inspection
        try:
            eb_packet_store.add(url, json.dumps(payload, ensure_ascii=False), r.text, status=r.status_code, note='auth error')
            try:
                with eb_packet_store._lock:
                    if len(eb_packet_store._deque) > 0:
                        eb_packet_store._deque[-1]['content_type'] = r.headers.get('content-type')
            except Exception:
                pass
        except Exception:
            pass
        raise RuntimeError(f"login failed: {r.status_code}")

    token = None
    try:
        token = _discover_token(r.json())
    except Exception:
        token = None

    if not token:
        raise RuntimeError("login succeeded but no token found in response")

    # persist token masked in logs
    settings["token"] = token
    cfg["settings"] = settings
    write_config(config_path, cfg)
    # record successful auth response for debugging/inspection
    try:
        eb_packet_store.add(url, json.dumps(payload, ensure_ascii=False), r.text, status=r.status_code, note='auth success')
        try:
            with eb_packet_store._lock:
                if len(eb_packet_store._deque) > 0:
                    eb_packet_store._deque[-1]['content_type'] = r.headers.get('content-type')
        except Exception:
            pass
    except Exception:
        pass
    logger.info("Easyberry: token persisted (masked) for user=%s", username)
    return token
