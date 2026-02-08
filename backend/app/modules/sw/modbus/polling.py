import logging
import threading
import time
import json	
import os
from typing import Callable, Dict, Optional, Tuple

from .modbus_tcp_client import MockModbusClient, TcpModbusClient
from .interfaces import IModbusTcpClient
from app.modules.sw.easyberry.store import database

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


# Packet log: thread-safe recent packet exchanges for debugging/inspection
class PacketStore:
    def __init__(self, maxlen: int = 1000):
        from collections import deque
        self._lock = threading.Lock()
        self._deque = deque(maxlen=maxlen)

    def add(self, poller_id: str, request_hex: Optional[str], response_hex: Optional[str], note: Optional[str] = None):
        import time
        entry = {
            'ts': time.time(),
            'poller_id': poller_id,
            'request': request_hex,
            'response': response_hex,
            'note': note,
            'status': None,
        }
        with self._lock:
            self._deque.append(entry)

    def get_last(self, limit: int = 200):
        with self._lock:
            items = list(self._deque)[-limit:]
            return [dict(i) for i in items]

    def clear(self):
        with self._lock:
            self._deque.clear()


packet_store = PacketStore(maxlen=2000)


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
        # fixed-period scheduling: run work immediately, then aim to run at start_time + n*interval
        next_run = time.time()
        while not self._stop_ev.is_set():
            # schedule next run based on fixed period
            next_run += self.interval
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
                    try:
                        packet_store.add(self._poller_id, rq_hex, rp_hex, note=None)
                        # mark successful exchange
                        try:
                            # last entry is the one we just added; set status to OK
                            with packet_store._lock:
                                if len(packet_store._deque) > 0:
                                    packet_store._deque[-1]['status'] = 'OK'
                        except Exception:
                            pass
                    except Exception:
                        logger.exception("Failed to add packet to packet_store")
                except Exception:
                    logger.exception("Failed to update status store")

                # update easyberry database if available and poller_id present
                try:
                    if res is not None and isinstance(res, (list, tuple)):
                        updated = database.update_from_poll_result(self._poller_id, list(res), meta={
                            "request": _format_hex_grouped(raw_req),
                            "response": _format_hex_grouped(raw_resp),
                            "base_address": int(self.address),
                        })
                        # always log how many things were updated for visibility
                        logger.info("Easyberry: poller=%s updated=%d things", self._poller_id, updated)
                except Exception:
                    logger.exception("Easyberry update failed")
                    
                #print(json.dumps(database.pollers))
                print(json.dumps(database.pollers, indent=2, ensure_ascii=False))
                    
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
                    try:
                        packet_store.add(self._poller_id, rq_hex, rp_hex, note=str(e))
                        # mark last packet as error
                        try:
                            with packet_store._lock:
                                if len(packet_store._deque) > 0:
                                    packet_store._deque[-1]['status'] = 'error'
                        except Exception:
                            pass
                    except Exception:
                        logger.exception("Failed to add packet to packet_store")
                except Exception:
                    logger.exception("Failed to update status store with error")
                try:
                    self.callback(None, e)
                except Exception:
                    logger.exception("Poller callback error handler failed")

            # wait until the next scheduled run (allow early exit)
            while not self._stop_ev.is_set():
                now = time.time()
                remaining = next_run - now
                if remaining <= 0:
                    break
                # sleep in small increments so we can exit quickly
                time.sleep(min(0.1, remaining))


def polling_example(config_path: str = "polling_config.json"):
    """Create manager and pollers from a polling configuration file.

    The configuration file is expected to contain a top-level `devices` list,
    each device may include a `pollers` list. Each poller will be created
    using the device's `unit_id` (poller `unit_id` entries are ignored).

    Returns: (manager, list_of_pollers)
    """
    cfg_path = config_path
    if not os.path.isabs(cfg_path):
        cfg_path = os.path.join(os.getcwd(), cfg_path)

    if not os.path.exists(cfg_path):
        logger.error("Polling config not found: %s", cfg_path)
        return None, []

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        logger.exception("Failed to load polling config %s: %s", cfg_path, e)
        return None, []

    manager = ModbusManager()
    pollers = []

    def cb(name):
        def _cb(res, err):
            if err:
                logger.warning("%s poll error: %s", name, err)
            else:
                logger.info("%s poll result: %s", name, res)
        return _cb

    for dev in cfg.get("devices", []):
        dev_id = dev.get("id") or "<unknown>"
        hw_mode = dev.get("hw_mode", "tcp")
        host = dev.get("host", "127.0.0.1")
        port = int(dev.get("port", 502))
        timeout = float(dev.get("timeout", 3.0))
        retries = int(dev.get("retries", 1))
        unit = int(dev.get("unit_id", 1))

        for pconf in dev.get("pollers", []):
            local_pid = pconf.get("id") or pconf.get("name") or f"poller-{len(pollers)+1}"
            if "unit_id" in pconf:
                logger.warning("Poller %s in device %s contains 'unit_id'; ignoring and using device unit_id=%s", local_pid, dev_id, unit)

            full_pid = f"{unit}-{local_pid}"

            client = manager.get_client(
                hw_mode=hw_mode,
                host=host,
                port=port,
                timeout=timeout,
                unit_id=unit,
                retries=retries,
            )

            poller = Poller(
                client,
                pconf.get("function", "holding"),
                address=int(pconf.get("address", 0)),
                count=int(pconf.get("count", 1)),
                interval=float(pconf.get("interval", 1.0)),
                callback=cb(full_pid),
                unit_id=unit,
                name=full_pid,
                poller_id=full_pid,
            )
            try:
                logger.info("Created poller %s interval=%s", full_pid, pconf.get("interval"))
                # also print to stdout to ensure visibility in all environments
                print(f"[polling-debug] Created poller {full_pid} interval={pconf.get('interval')}")
            except Exception:
                pass
            pollers.append(poller)

    for p in pollers:
        try:
            p.start()
            logger.info("Started poller %s interval=%s", getattr(p, 'name', None), getattr(p, 'interval', None))
            # print to stdout as well for immediate feedback in consoles
            try:
                print(f"[polling-debug] Started poller {getattr(p, 'name', None)} interval={getattr(p, 'interval', None)}")
            except Exception:
                pass
        except Exception:
            logger.exception("Failed to start poller %s", getattr(p, 'name', None))

    return manager, pollers


# Example polling controller (start/stop) for debug endpoints
_example_manager = None
_example_pollers = None

def start_example_polling():
    global _example_manager, _example_pollers
    if _example_manager is not None:
        return False
    manager, pollers = polling_example()
    _example_manager = manager
    _example_pollers = pollers
    return True


def stop_example_polling():
    global _example_manager, _example_pollers
    if _example_manager is None:
        return False
    try:
        for p in (_example_pollers or []):
            try:
                p.stop()
            except Exception:
                pass
        # give threads a short time to exit
        time.sleep(0.2)
        try:
            _example_manager.close_all()
        except Exception:
            pass
    finally:
        _example_manager = None
        _example_pollers = None
    return True


def example_polling_status() -> bool:
    return _example_manager is not None
