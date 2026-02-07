import json
import threading
import time
from typing import Dict, List, Optional, Tuple, Any

import logging
logger = logging.getLogger(__name__)

from .error_logger import ErrorLogger


class Database:
    def __init__(self):
        self._lock = threading.RLock()
        # raw representation loaded from config
        self.pollers: List[Dict[str, Any]] = []
        # mbid -> (poller_id, thing_dict)
        self.mbid_index: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        self._error_logger = ErrorLogger()

    def load_from_dict(self, cfg: Dict[str, Any]) -> None:
        with self._lock:
            self.pollers = cfg.get("pollers", [])
            # ensure each poller has an id
            for p in self.pollers:
                if "id" not in p:
                    p.setdefault("id", f"poller-{int(time.time()*1000)}")
                p.setdefault("things", [])
            self._build_index()

    def _build_index(self) -> None:
        idx: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        for p in self.pollers:
            pid = p.get("id")
            for t in p.get("things", []):
                mbid = str(t.get("mbid"))
                if not mbid:
                    continue
                idx[mbid] = (pid, t)
        self.mbid_index = idx
        logger.info("Easyberry: built mbid index with %d entries", len(self.mbid_index))

    def get_pollers(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.pollers)

    def get_thing_by_mbid(self, mbid: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        with self._lock:
            return self.mbid_index.get(str(mbid))

    def update_thing_value_by_mbid(self, mbid: str, new_value: Any, meta: Optional[Dict] = None) -> bool:
        mbid_s = str(mbid)
        with self._lock:
            entry = self.mbid_index.get(mbid_s)
            if not entry:
                # log missing mbid
                self._error_logger.log_missing_mbid(mbid_s, meta)
                return False
            pid, thing = entry
            # update fields
            thing["value"] = new_value
            thing["updated_at"] = time.time()
            if meta:
                thing.setdefault("meta", {}).update(meta)
            return True

    def update_from_poll_result(self, poller_id: str, values: List[Any], meta: Optional[Dict] = None) -> int:
        """Update things for a poller using their configured `register_index`.

        Expects each thing in poller to have optional `register_index` int.
        Returns number of things updated.
        """
        updated = 0
        with self._lock:
            # First, attempt to update using poller's configured `register_index` if the poller is known
            poller = next((p for p in self.pollers if p.get("id") == poller_id), None)
            updated_mbids = set()
            if poller:
                for thing in poller.get("things", []):
                    ri = thing.get("register_index")
                    if ri is None:
                        continue
                    try:
                        val = values[int(ri)]
                    except Exception:
                        continue
                    mbid_s = str(thing.get("mbid"))
                    if self.update_thing_value_by_mbid(mbid_s, val, meta=meta):
                        updated += 1
                        updated_mbids.add(mbid_s)

            # Secondly, if meta provides a base_address, try matching mbid == absolute_address
            # (absolute_address = base_address + index). This allows updating things by 'mbid'
            # when register_index is not configured.
            base = None
            try:
                if meta and "base_address" in meta:
                    base = int(meta.get("base_address"))
            except Exception:
                base = None

            if base is not None:
                for idx, val in enumerate(values):
                    abs_addr = str(base + int(idx))
                    if abs_addr in updated_mbids:
                        continue
                    if self.update_thing_value_by_mbid(abs_addr, val, meta=meta):
                        updated += 1
                        updated_mbids.add(abs_addr)
        return updated


# global shared database
database = Database()
