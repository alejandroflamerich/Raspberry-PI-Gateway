import logging
import time
import json
from typing import Dict, Any, Optional

import httpx

from .config import read_config, write_config
from .packet_store import eb_packet_store

logger = logging.getLogger(__name__)


def _discover_token(resp_json: Dict[str, Any]) -> Optional[str]:
    # support common token fields and nested shapes (e.g. {data: {token: ...}})
    keys = ("token", "access_token", "jwt", "accessToken")

    def _search(obj) -> Optional[str]:
        if obj is None:
            return None
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in keys and v:
                    return str(v)
            for v in obj.values():
                try:
                    res = _search(v)
                    if res:
                        return res
                except Exception:
                    continue
        elif isinstance(obj, list):
            for it in obj:
                try:
                    res = _search(it)
                    if res:
                        return res
                except Exception:
                    continue
        return None

    return _search(resp_json)


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

    # perform HTTP request
    try:
        logger.info("%s - LOGIN_REQUEST - url=%s - payload=%s", ts, url, json.dumps(masked, ensure_ascii=False))
        with httpx.Client(timeout=10.0) as client:
            # send username/password as JSON per spec
            r = client.post(url, json=payload)
    except Exception as e:
        logger.exception("Easyberry login failed: %s", e)
        # record failed auth attempt in easyberry packet store
        try:
            eb_packet_store.add(url, json.dumps(payload, ensure_ascii=False), None, status=None, note=str(e))
        except Exception:
            pass
        # also append failure info to backend/message.log
        try:
            from pathlib import Path
            root = Path(__file__).resolve().parents[4]
            msg_path = root / 'message.log'
            entry = {
                'ts': time.time(),
                'op': 'login',
                'url': url,
                'payload': payload,
                'request_headers': None,
                'response_headers': None,
                'status': None,
                'response': None,
                'error': str(e),
            }
            try:
                with msg_path.open('a', encoding='utf-8') as mf:
                    mf.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception:
                pass
        except Exception:
            pass
        raise

    # record the raw response so frontend can inspect it even if token is missing
    try:
        req_headers = None
        resp_headers = None
        try:
            req_headers = dict(r.request.headers) if getattr(r, 'request', None) is not None else None
        except Exception:
            req_headers = None
        try:
            resp_headers = dict(r.headers)
        except Exception:
            resp_headers = None

        eb_packet_store.add(url, json.dumps(payload, ensure_ascii=False), r.text, request_headers=req_headers, response_headers=resp_headers, status=r.status_code, note='auth raw')
        try:
            with eb_packet_store._lock:
                if len(eb_packet_store._deque) > 0:
                    eb_packet_store._deque[-1]['content_type'] = r.headers.get('content-type')
        except Exception:
            pass

        # append a short record to backend/message.log for easier debugging
        try:
            from pathlib import Path
            root = Path(__file__).resolve().parents[4]
            msg_path = root / 'message.log'
            entry = {
                'ts': time.time(),
                'op': 'login',
                'url': url,
                'payload': payload,
                'request_headers': req_headers,
                'response_headers': resp_headers,
                'status': getattr(r, 'status_code', None),
                'response': r.text if getattr(r, 'text', None) is not None else None,
            }
            try:
                with msg_path.open('a', encoding='utf-8') as mf:
                    mf.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception:
                pass
        except Exception:
            pass
    except Exception:
        pass

    # Also persist the last auth response to a debug file for easier inspection during development.
    try:
        from pathlib import Path
        root = Path(__file__).resolve().parents[4]
        dbg_path = root / 'easyberry_last_auth.json'
        try:
            dbg_path.write_text(r.text or '', encoding='utf-8')
        except Exception:
            # best-effort only
            pass
    except Exception:
        pass

    if r.status_code != 200:
        logger.error("Easyberry login failed status=%s body=%s", r.status_code, (r.text or '')[:200])
        # record response in packet store for inspection
        try:
            req_headers = None
            resp_headers = None
            try:
                req_headers = dict(r.request.headers) if getattr(r, 'request', None) is not None else None
            except Exception:
                req_headers = None
            try:
                resp_headers = dict(r.headers)
            except Exception:
                resp_headers = None

            eb_packet_store.add(url, json.dumps(payload, ensure_ascii=False), r.text, request_headers=req_headers, response_headers=resp_headers, status=r.status_code, note='auth error')
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
        req_headers = None
        resp_headers = None
        try:
            req_headers = dict(r.request.headers) if getattr(r, 'request', None) is not None else None
        except Exception:
            req_headers = None
        try:
            resp_headers = dict(r.headers)
        except Exception:
            resp_headers = None

        eb_packet_store.add(url, json.dumps(payload, ensure_ascii=False), r.text, request_headers=req_headers, response_headers=resp_headers, status=r.status_code, note='auth success')
        try:
            with eb_packet_store._lock:
                if len(eb_packet_store._deque) > 0:
                    eb_packet_store._deque[-1]['content_type'] = r.headers.get('content-type')
                    eb_packet_store._deque[-1]['request_headers'] = req_headers
                    eb_packet_store._deque[-1]['response_headers'] = resp_headers
        except Exception:
            pass
    except Exception:
        pass

    logger.info("Easyberry: token persisted (masked) for user=%s", username)
    return token
