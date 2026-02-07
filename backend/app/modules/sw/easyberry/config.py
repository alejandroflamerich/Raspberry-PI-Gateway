import json
import os
import tempfile
from typing import Any, Dict


def read_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg


def _validate_config(cfg: Dict[str, Any]) -> None:
    settings = cfg.get("settings")
    if not isinstance(settings, dict):
        raise ValueError("missing 'settings' in config")
    if not settings.get("url"):
        raise ValueError("settings.url is required")
    if not settings.get("username"):
        raise ValueError("settings.username is required")
    if not settings.get("password"):
        raise ValueError("settings.password is required")


def write_config(path: str, cfg: Dict[str, Any]) -> None:
    # validate minimal structure before persisting
    _validate_config(cfg)
    dirn = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".tmp-config-", dir=dirn)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        # atomic replace
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
