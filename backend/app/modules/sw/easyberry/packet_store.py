import threading
from collections import deque
from typing import Optional
import logging
import uuid

logger = logging.getLogger(__name__)


class EasyberryPacketStore:
    def __init__(self, maxlen: int = 500):
        self._lock = threading.Lock()
        self._deque = deque(maxlen=maxlen)

    def add(self, endpoint: str, request_body: Optional[str], response_body: Optional[str], status: Optional[int] = None, note: Optional[str] = None):
        import time
        entry = {
            'id': str(uuid.uuid4()),
            'ts': time.time(),
            'endpoint': endpoint,
            'request': request_body,
            'response': response_body,
            'request_headers': None,
            'response_headers': None,
            'content_type': None,
            'status': status,
            'note': note,
        }
        with self._lock:
            self._deque.append(entry)
            try:
                logger.info("Easyberry: packet added endpoint=%s status=%s note=%s", endpoint, status, note)
            except Exception:
                pass

    def get_last(self, limit: int = 200):
        with self._lock:
            items = list(self._deque)[-limit:]
            return [dict(i) for i in items]

    def clear(self):
        with self._lock:
            self._deque.clear()


eb_packet_store = EasyberryPacketStore()
