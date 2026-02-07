import logging
from typing import Dict, Any, Tuple

import httpx

from .config import read_config
from .packet_store import eb_packet_store

logger = logging.getLogger(__name__)


def build_endpoint_from_config(cfg: Dict[str, Any]) -> str:
    settings = cfg.get("settings", {})
    base = settings.get("url", "").rstrip("/")
    context = settings.get("context", "")
    # The endpoint is exactly settings.url + settings.context (user-specified).
    if context:
        # ensure single slash between parts
        return f"{base}/{context.lstrip('/') }"
    return base


def send_put(config_path: str, payload: Dict[str, Any]) -> Tuple[int, str]:
    cfg = read_config(config_path)
    settings = cfg.get("settings", {})
    token = settings.get("token")
    endpoint = build_endpoint_from_config(cfg)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    logger.info("Easyberry: sending PUT to %s", endpoint)
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(endpoint, json=payload, headers=headers)
    except Exception as e:
        logger.exception("transport error: %s", e)
        # record exception in easyberry packet store
        try:
            eb_packet_store.add(endpoint, json.dumps(payload, ensure_ascii=False), None, status=None, note=str(e))
        except Exception:
            pass
        raise

    # record successful exchange
    try:
        import json as _json
        req_body = _json.dumps(payload, ensure_ascii=False)
    except Exception:
        req_body = str(payload)
    try:
        # capture content-type header when present
        ctype = None
        try:
            ctype = r.headers.get('content-type')
        except Exception:
            ctype = None
        # store request and response bodies and headers
        try:
            resp_headers = None
            try:
                resp_headers = dict(r.headers)
            except Exception:
                resp_headers = None
            eb_packet_store.add(endpoint, req_body, r.text, status=r.status_code, note=None)
            try:
                with eb_packet_store._lock:
                    if len(eb_packet_store._deque) > 0:
                        eb_packet_store._deque[-1]['content_type'] = ctype
                        eb_packet_store._deque[-1]['request_headers'] = headers
                        eb_packet_store._deque[-1]['response_headers'] = resp_headers
            except Exception:
                pass
        except Exception:
            pass
    except Exception:
        pass

    return r.status_code, r.text
