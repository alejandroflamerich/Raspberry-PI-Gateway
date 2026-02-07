import logging
import threading
import time
from typing import Callable, Dict, Optional, Tuple

from app.modules.sw.modbus import MockModbusClient, TcpModbusClient, IModbusTcpClient

logger = logging.getLogger(__name__)


def _format_hex_grouped(raw: Optional[bytes]) -> Optional[str]:
    if raw is None:
        return None
    try:
        return " ".join(f"0x{b:02x}" for b in raw)
    except Exception:
        try:
            # handle bytearray or other sequence
            return " ".join(f"0x{int(b):02x}" for b in raw)
        except Exception:
            return None


class StatusStore:
    """Thread-safe in-memory store of poller statuses.

    Stored fields per poller id:
      - last_value: Optional[list]
      - last_error: Optional[str]
      - last_request: dict (function/address/count/unit_id)
      - last_updated: timestamp
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._data: Dict[str, Dict] = {}

    def update(self, poller_id: str, *, last_value=None, last_error: Optional[str] = None, last_request: Optional[Dict] = None):
        import time
        with self._lock:
            item = self._data.get(poller_id, {})
            if last_request is not None:
                item['last_request'] = last_request
            if last_value is not None:
                item['last_value'] = last_value
                item['last_error'] = None
            if last_error is not None:
                item['last_error'] = last_error
            # allow raw hex fields to be passed in last_request (raw_request_hex/raw_response_hex)
            if last_request and isinstance(last_request, dict):
                raw_req = last_request.get('raw_request_hex')
                raw_resp = last_request.get('raw_response_hex')
                if raw_req is not None:
                    item['raw_request_hex'] = raw_req
                if raw_resp is not None:
                    item['raw_response_hex'] = raw_resp
            item['last_updated'] = time.time()
            self._data[poller_id] = item

    def get_all(self) -> Dict[str, Dict]:
        with self._lock:
            # return a shallow copy
            return {k: dict(v) for k, v in self._data.items()}


# default global store that can be used by Poller instances
default_store = StatusStore()


class ModbusManager:
    """Manage Modbus client instances keyed by connection params.

    This allows reusing a single TCP connection for multiple pollers
    or creating separate connections when desired.
    """

    def __init__(self):
        self._clients: Dict[Tuple[str, int, int, float, int], IModbusTcpClient] = {}
        self._lock = threading.Lock()

    def _key_for(self, host: str, port: int, unit_id: int, timeout: float, retries: int):
        return (host, port, unit_id, float(timeout), int(retries))

    def get_client(self, hw_mode: str = "mock", host: str = "localhost", port: int = 502,
                   timeout: float = 3.0, unit_id: int = 1, retries: int = 1) -> IModbusTcpClient:
        if hw_mode == "mock":
            return MockModbusClient()

        key = self._key_for(host, port, unit_id, timeout, retries)
        with self._lock:
            if key not in self._clients:
                client = TcpModbusClient(host=host, port=port, timeout=timeout, unit_id=unit_id, retries=retries)
                try:
                    client.connect()
                except Exception as e:
                    logger.warning("Failed initial connect for %s:%s -> %s", host, port, e)
                self._clients[key] = client
            return self._clients[key]

    def close_all(self) -> None:
        with self._lock:
            for c in list(self._clients.values()):
                try:
                    c.close()
                except Exception:
                    pass
            self._clients.clear()


class Poller(threading.Thread):
    """Poll registers periodically and call a user callback with results.

    callback signature: callback(result: Optional[list[int]], error: Optional[Exception])
    """

    def __init__(self,
                 client: IModbusTcpClient,
                 function: str,
                 address: int,
                 count: int,
                 interval: float,
                 callback: Callable[[Optional[list], Optional[Exception]], None],
                 unit_id: Optional[int] = None,
                 name: Optional[str] = None,
                 status_store: Optional[StatusStore] = None,
                 poller_id: Optional[str] = None):
        super().__init__(daemon=True)
        self.client = client
        self.function = function  # 'holding' or 'input'
        self.address = address
        self.count = count
        self.interval = float(interval)
        self.callback = callback
        self.unit_id = unit_id
        self._stop_ev = threading.Event()
        if name:
            self.name = name
        # status store to report last values/errors
        self._status_store = status_store or default_store
        # unique id to identify this poller in the store
        self._poller_id = poller_id or getattr(self, 'name', None) or f"poller-{id(self)}"
        # initialize status
        try:
            self._status_store.update(self._poller_id, last_request={
                'function': self.function,
                'address': self.address,
                'count': self.count,
                'unit_id': self.unit_id,
            })
        except Exception:
            pass

    def stop(self) -> None:
        self._stop_ev.set()

    def stopped(self) -> bool:
        return self._stop_ev.is_set()

    def run(self) -> None:
        while not self._stop_ev.is_set():
            try:
                if self.function == "holding":
                    res = self.client.read_holding_registers(self.address, self.count, unit_id=self.unit_id)
                elif self.function == "input":
                    res = self.client.read_input_registers(self.address, self.count, unit_id=self.unit_id)
                else:
                    raise ValueError("Unknown function: %s" % (self.function,))
                # update status store including raw request/response if available
                try:
                    raw_req = getattr(self.client, '_last_request', None)
                    raw_resp = getattr(self.client, '_last_response', None)
                    last_req_info = {
                        'function': self.function,
                        'address': self.address,
                        'count': self.count,
                        'unit_id': self.unit_id,
                    }
                    rq_hex = _format_hex_grouped(raw_req)
                    rp_hex = _format_hex_grouped(raw_resp)
                    if rq_hex is not None:
                        last_req_info['raw_request_hex'] = rq_hex
                    if rp_hex is not None:
                        last_req_info['raw_response_hex'] = rp_hex
                    self._status_store.update(self._poller_id, last_value=res, last_request=last_req_info)
                except Exception:
                    logger.exception("Failed to update status store")
                try:
                    self.callback(res, None)
                except Exception:
                    logger.exception("Poller callback failed")
            except Exception as e:
                # record error in store and notify callback
                try:
                    raw_req = getattr(self.client, '_last_request', None)
                    raw_resp = getattr(self.client, '_last_response', None)
                    last_req_info = {
                        'function': self.function,
                        'address': self.address,
                        'count': self.count,
                        'unit_id': self.unit_id,
                    }
                    rq_hex = _format_hex_grouped(raw_req)
                    rp_hex = _format_hex_grouped(raw_resp)
                    if rq_hex is not None:
                        last_req_info['raw_request_hex'] = rq_hex
                    if rp_hex is not None:
                        last_req_info['raw_response_hex'] = rp_hex
                    self._status_store.update(self._poller_id, last_error=str(e), last_request=last_req_info)
                except Exception:
                    logger.exception("Failed to update status store with error")
                try:
                    self.callback(None, e)
                except Exception:
                    logger.exception("Poller callback error handler failed")
            # sleep with early exit
            slept = 0.0
            step = 0.1
            while slept < self.interval and not self._stop_ev.is_set():
                time.sleep(min(step, self.interval - slept))
                slept += step


def polling_example():
    """Example: create manager, multiple pollers (digital/analog/mixed).

    Returns: (manager, list_of_pollers)
    """
    manager = ModbusManager()

    def cb(name):
        def _cb(res, err):
            if err:
                logger.warning("%s poll error: %s", name, err)
            else:
                logger.info("%s poll result: %s", name, res)
        return _cb

    # shared connection example
    client = manager.get_client(hw_mode="tcp", host="127.0.0.1", port=502, timeout=2.0, unit_id=1)

    p1 = Poller(client, "holding", address=0, count=4, interval=1.0, callback=cb("analog-1"), name="analog-1")
    p2 = Poller(client, "input", address=100, count=2, interval=2.0, callback=cb("digital-1"), name="digital-1")

    # separate connection (different unit id or host)
    client2 = manager.get_client(hw_mode="tcp", host="127.0.0.1", port=502, timeout=2.0, unit_id=2)
    p3 = Poller(client2, "holding", address=200, count=2, interval=0.5, callback=cb("mixed-1"), name="mixed-1")

    for p in (p1, p2, p3):
        p.start()

    return manager, [p1, p2, p3]
