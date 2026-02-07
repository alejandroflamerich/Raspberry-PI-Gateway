import json
from typing import Dict
from .store import database


def load_from_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    database.load_from_dict(cfg)
