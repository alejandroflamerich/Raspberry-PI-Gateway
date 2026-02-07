import time
import threading
import os
from typing import Optional, Dict

DEFAULT_LOG = "error.log"


class ErrorLogger:
    def __init__(self, path: Optional[str] = None, dedupe_window: int = 60):
        # if path is None, compute relative to current working dir at log time
        self._path = path
        self._lock = threading.Lock()
        self._dedupe_window = dedupe_window
        # mbid -> last_ts
        self._last_logged: Dict[str, float] = {}

    def log_missing_mbid(self, mbid: str, context: Optional[Dict] = None) -> None:
        ts = time.time()
        now = ts
        with self._lock:
            last = self._last_logged.get(mbid)
            if last and (now - last) < self._dedupe_window:
                # skip to avoid spam
                return
            self._last_logged[mbid] = now
            line = f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))} - MBID_NOT_FOUND - {mbid}"
            if context:
                try:
                    import json

                    line += " - " + json.dumps(context, ensure_ascii=False)
                except Exception:
                    line += " - (context serialization failed)"
            line += "\n"
            path = self._path or os.path.join(os.getcwd(), DEFAULT_LOG)
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
