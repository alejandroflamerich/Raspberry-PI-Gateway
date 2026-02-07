import logging
import time
from typing import Dict, Any

from .config import read_config
from .transport import send_put
from .auth import login_and_persist_token

logger = logging.getLogger(__name__)


def build_payload_from_database(database) -> Dict[str, Any]:
    # database is expected to provide get_pollers() which contains things with 'name' and 'value'
    things: Dict[str, Dict[str, str]] = {}
    for p in database.get_pollers():
        for t in p.get("things", []):
            name = t.get("name")
            if name is None:
                continue
            val = t.get("value")
            things[name] = {"value": str(val) if val is not None else ""}
    return {"op": "put", "things": things}


def run_once(config_path: str, database) -> None:
    cfg = read_config(config_path)
    payload = build_payload_from_database(database)
    try:
        status, body = send_put(config_path, payload)
    except Exception as e:
        logger.exception("Failed to send payload: %s", e)
        return

    if status in (401, 403):
        logger.info("Received %s, refreshing token and retrying once", status)
        try:
            login_and_persist_token(config_path)
        except Exception as e:
            logger.exception("Re-login failed: %s", e)
            return
        try:
            status2, body2 = send_put(config_path, payload)
            logger.info("Retry status=%s", status2)
        except Exception as e:
            logger.exception("Retry failed: %s", e)
    else:
        logger.info("Send result status=%s", status)


def run_loop(config_path: str, database, stop_event=None) -> None:
    cfg = read_config(config_path)
    duration = cfg.get("duration", 30)
    while True:
        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
            logger.info("run_loop: stop event set, exiting")
            break
        run_once(config_path, database)
        time.sleep(duration)
