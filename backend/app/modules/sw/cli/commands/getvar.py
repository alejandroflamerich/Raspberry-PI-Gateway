from ..registry import register_command
from typing import Any, Dict
from pathlib import Path
import json
import os


def _serialize_packet_list(items):
    out = []
    for it in items:
        # keep basic fields and convert ts to float if present
        o = {
            'endpoint': it.get('endpoint'),
            'status': it.get('status'),
            'content_type': it.get('content_type'),
            'request': it.get('request'),
            'response': it.get('response'),
            'note': it.get('note'),
        }
        try:
            o['ts'] = float(it.get('ts'))
        except Exception:
            o['ts'] = it.get('ts')
        out.append(o)
    return out


def handler(args: Dict[str, Any], context=None):
    raw = args.get('name') or args.get('var')
    if not raw:
        raise ValueError('missing variable name')

    # tokenize allowing dotted path and bracket numeric indexes, e.g.:
    #  - database.pollers.0  (existing form)
    #  - database.pollers[0] (supported by the tokenizer below)
    def _tokenize(s: str):
        tokens = []
        cur = ''
        i = 0
        while i < len(s):
            c = s[i]
            if c == '.':
                if cur:
                    tokens.append(cur)
                    cur = ''
                i += 1
                continue
            if c == '[':
                if cur:
                    tokens.append(cur)
                    cur = ''
                # read until closing bracket
                i += 1
                num = ''
                while i < len(s) and s[i] != ']':
                    num += s[i]
                    i += 1
                if i >= len(s) or s[i] != ']':
                    raise ValueError('malformed variable name: missing ]')
                tokens.append(num)
                i += 1
                continue
            cur += c
            i += 1
        if cur:
            tokens.append(cur)
        return tokens

    parts = _tokenize(raw)
    base = parts[0]
    tail = parts[1:]

    # helper to traverse
    def _traverse(obj, parts_list):
        cur = obj
        for p in parts_list:
            if cur is None:
                raise KeyError(f'path not found: {".".join(parts_list)}')
            # numeric index access for lists
            if isinstance(cur, list):
                try:
                    idx = int(p)
                except Exception:
                    raise KeyError(f'expected numeric index for list access, got: {p}')
                if idx < 0 or idx >= len(cur):
                    raise KeyError(f'index out of range: {p}')
                cur = cur[idx]
                continue
            # dict access
            try:
                cur = cur[p]
                continue
            except Exception:
                # try attribute access
                try:
                    cur = getattr(cur, p)
                    continue
                except Exception:
                    raise KeyError(f'path not found segment: {p}')
        return cur

    # resolve base variable (whitelist)
    if base == 'database':
        try:
            from app.modules.sw.easyberry.store import database
            obj = {'pollers': database.get_pollers(), 'mbid_index': {k: {'poller_id': v[0], 'thing': v[1]} for k, v in getattr(database, 'mbid_index', {}).items()}}
        except Exception as e:
            raise RuntimeError(f'failed reading database: {e}')
    elif base in ('easyberry', 'easyberry_packets'):
        try:
            from app.modules.sw.easyberry.packet_store import eb_packet_store
            obj = _serialize_packet_list(eb_packet_store.get_last(limit=200))
        except Exception as e:
            raise RuntimeError(f'failed reading easyberry packets: {e}')
    elif base == 'settings':
        # read easyberry_config.json from the backend repository root if present
        try:
            p = Path(__file__).resolve()
            root = p
            # walk up until we find a folder named 'backend' or reach filesystem root
            while root.name != 'backend' and root.parent != root:
                root = root.parent
            cfg_path = root / 'easyberry_config.json'
            if not cfg_path.exists():
                # fallback to cwd
                cfg_path = Path(os.getcwd()) / 'easyberry_config.json'
            text = cfg_path.read_text(encoding='utf-8')
            data = json.loads(text)
            # return the 'settings' object if present, otherwise whole file
            obj = data.get('settings', data)
        except Exception as e:
            raise RuntimeError(f'failed reading settings: {e}')
    elif base in ('last-auth', 'last_auth', 'easyberry_last_auth'):
        # read backend/easyberry_last_auth.json which contains last auth response body
        try:
            p = Path(__file__).resolve()
            root = p
            while root.name != 'backend' and root.parent != root:
                root = root.parent
            last_path = root / 'easyberry_last_auth.json'
            if not last_path.exists():
                last_path = Path(os.getcwd()) / 'easyberry_last_auth.json'
            text = last_path.read_text(encoding='utf-8')
            # Note: the file may contain a raw JSON object or plain text; attempt parse
            try:
                obj = json.loads(text)
            except Exception:
                obj = {'raw': text}
        except Exception as e:
            raise RuntimeError(f'failed reading last-auth file: {e}')
    elif base in ('packets', 'modbus_packets'):
        try:
            from app.modules.sw.modbus.polling import packet_store
            items = packet_store.get_last(limit=200)
            obj = [{
                'ts': float(it.get('ts')) if it.get('ts') is not None else None,
                'poller_id': it.get('poller_id'),
                'status': it.get('status'),
                'request': it.get('request'),
                'response': it.get('response'),
                'note': it.get('note'),
            } for it in items]
        except Exception as e:
            raise RuntimeError(f'failed reading modbus packets: {e}')
    else:
        raise KeyError(f'unknown variable: {base}')

    if not tail:
        return obj

    try:
        return _traverse(obj, tail)
    except KeyError as ke:
        raise KeyError(str(ke))


register_command('getvar', handler, description='Get a whitelisted backend variable (database, easyberry, packets)', args_schema={'name': 'str'})
