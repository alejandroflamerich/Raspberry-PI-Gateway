import argparse
import json
from typing import Any, Dict

from .store import database
from .loader import load_from_file


def _serialize_db() -> Dict[str, Any]:
    # produce a JSON-serializable snapshot of the database
    pollers = database.get_pollers()
    mbid_index = {}
    for k, v in getattr(database, "mbid_index", {}).items():
        pid, thing = v
        mbid_index[k] = {"poller_id": pid, "thing": thing}
    return {"pollers": pollers, "mbid_index": mbid_index}


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the Easyberry in-memory database")
    parser.add_argument("--load-config", "-c", help="Optional JSON config to load before printing")
    args = parser.parse_args()

    if args.load_config:
        try:
            load_from_file(args.load_config)
        except Exception as e:
            print(f"Failed to load config: {e}")
            return

    snapshot = _serialize_db()
    print(json.dumps(snapshot, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
