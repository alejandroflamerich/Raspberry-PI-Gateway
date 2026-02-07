import argparse
import json
from typing import Any

from .store import database


def _resolve_path(root: Any, path: str, max_items: int = 100, depth: int = 10):
    # simple dot and [index] parser
    cur = root
    if not path or path == "database":
        return cur
    parts = []
    buf = ""
    i = 0
    while i < len(path):
        c = path[i]
        if c == ".":
            if buf:
                parts.append(buf)
                buf = ""
            i += 1
            continue
        if c == "[":
            # flush buf
            if buf:
                parts.append(buf)
                buf = ""
            j = path.find("]", i)
            if j == -1:
                raise ValueError("Unmatched '[' in path")
            parts.append(path[i : j + 1])
            i = j + 1
            continue
        buf += c
        i += 1
    if buf:
        parts.append(buf)

    for p in parts:
        if isinstance(cur, (list, tuple)) and p.startswith("[") and p.endswith("]"):
            idx = int(p[1:-1])
            cur = cur[idx]
        elif p.startswith("[") and p.endswith("]"):
            raise ValueError("Indexing into non-list")
        else:
            cur = getattr(cur, p, None) if hasattr(cur, p) else (cur.get(p) if isinstance(cur, dict) else None)
        if cur is None:
            raise KeyError(f"Path segment not found: {p}")
    return cur


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="database", help="Path to inspect (eg: database.pollers[0].things)")
    parser.add_argument("--depth", type=int, default=10)
    parser.add_argument("--max-items", type=int, default=200)
    args = parser.parse_args()

    root = {"database": database}
    try:
        res = _resolve_path(root, args.path)
    except Exception as e:
        print(f"Error resolving path: {e}")
        return
    # prepare pretty JSON serializable
    def default(o):
        try:
            import time

            return str(o)
        except Exception:
            return repr(o)

    print(json.dumps(res, default=default, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
