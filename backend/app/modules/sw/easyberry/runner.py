import threading
import os
import logging
from typing import Optional

from .connector import run_loop

logger = logging.getLogger(__name__)

# module-level runner state
_thread: Optional[threading.Thread] = None
_stop_event: Optional[threading.Event] = None


def _config_path():
    return os.path.join(os.getcwd(), "easyberry_config.json")


def start():
    global _thread, _stop_event
    if _thread and _thread.is_alive():
        return False
    _stop_event = threading.Event()
    cfg_path = _config_path()
    t = threading.Thread(target=run_loop, args=(cfg_path, __import__('app.modules.sw.easyberry.store', fromlist=['database']).modules.sw.easyberry.store.database if False else __import__('app.modules.sw.easyberry.store', fromlist=['database']).database, _stop_event), daemon=True)
    # The above import trick is to avoid circular import at module load; simpler: import inside target by using run_loop which accepts database
    # But we need to pass the database instance; import here properly
    try:
        from app.modules.sw.easyberry.store import database
        t = threading.Thread(target=run_loop, args=(cfg_path, database, _stop_event), daemon=True)
    except Exception:
        t = threading.Thread(target=run_loop, args=(cfg_path, None, _stop_event), daemon=True)

    _thread = t
    t.start()
    logger.info("Easyberry runner started")
    return True


def stop():
    global _thread, _stop_event
    if _stop_event:
        _stop_event.set()
    _thread = None
    _stop_event = None
    logger.info("Easyberry runner stopped")
    return True


def status() -> dict:
    return {"running": bool(_thread and _thread.is_alive())}
