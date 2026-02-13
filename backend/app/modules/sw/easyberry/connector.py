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
    # keep compatibility: run_once performs a send but does not return results
    try:
        send_once(config_path, database)
    except Exception:
        # send_once already logs
        pass


def send_once(config_path: str, database) -> tuple:
    """Build payload from `database` and send it once. Returns (status_code, body).

    If a 401/403 is received, attempts one re-login and retry.
    """
    cfg = read_config(config_path)
    payload = build_payload_from_database(database)
    try:
        status, body = send_put(config_path, payload)
    except Exception as e:
        logger.exception("Failed to send payload: %s", e)
        raise

    if status in (401, 403):
        logger.info("Received %s, refreshing token and retrying once", status)
        try:
            login_and_persist_token(config_path)
        except Exception as e:
            logger.exception("Re-login failed: %s", e)
            return status, body
        try:
            status2, body2 = send_put(config_path, payload)
            logger.info("Retry status=%s", status2)
            return status2, body2
        except Exception as e:
            logger.exception("Retry failed: %s", e)
            raise
    else:
        logger.info("Send result status=%s", status)
        return status, body


def run_loop(config_path: str, database, stop_event=None) -> None:
    cfg = read_config(config_path)
    duration = cfg.get("duration", 30)
    iteration = 0
    # Keep running until an external stop_event is set by the runner.stop() call.
    # Use stop_event.wait(timeout) when available so the loop is interruptible
    # and will stop promptly when the stop button is pressed.
    while True:
        iteration += 1
        logger.debug("run_loop: starting iteration %d", iteration)
        if stop_event is not None and getattr(stop_event, "is_set", lambda: False)():
            logger.info("run_loop: stop event set, exiting")
            break
        try:
            run_once(config_path, database)
        except Exception:
            # run_once already logs failures; continue looping so polling remains active
            logger.exception("run_loop: run_once failed, continuing loop")
        else:
            logger.debug("run_loop: iteration %d completed successfully", iteration)

        # If a stop_event was provided, prefer waiting on it (interruptible).
        if stop_event is not None:
            # If duration is falsy (0, None, negative) wait indefinitely until stop
            try:
                if duration is None or (isinstance(duration, (int, float)) and duration <= 0):
                    logger.debug("run_loop: waiting indefinitely until stop_event")
                    stop_event.wait()
                    # loop will re-check is_set at top and exit
                else:
                    stop_event.wait(duration)
            except Exception:
                # In case stop_event.wait isn't available for some reason, fallback to sleep
                time.sleep(duration if duration and duration > 0 else 1)
        else:
            # No stop_event available; fall back to sleeping
            try:
                time.sleep(duration if duration and duration > 0 else 1)
            except Exception:
                # ignore sleep interruptions and continue
                pass
