import threading
import time
from typing import Callable, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# registry record: name -> (handler, description, args_schema)
_registry: Dict[str, Tuple[Callable[[Dict[str, Any]], Any], str, Optional[Dict[str, Any]]]] = {}
_started_at = time.time()

# Limits
DEFAULT_TIMEOUT = 5.0
MAX_OUTPUT_CHARS = 10000


def register_command(name: str, handler: Callable[[Dict[str, Any]], Any], description: str = "", args_schema: Optional[Dict[str, Any]] = None):
    _registry[name] = (handler, description or "", args_schema)


def list_commands():
    out = []
    for k, v in _registry.items():
        _, desc, schema = v
        out.append({"name": k, "description": desc, "args_schema": schema})
    return out


def _run_with_timeout(fn, args, timeout):
    result = {}

    def target():
        try:
            result['value'] = fn(args)
        except Exception as e:
            result['error'] = str(e)

    t = threading.Thread(target=target)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return {'timeout': True}
    return result


def _call_handler(handler, args, context):
    # Try calling handler with (args, context), fall back to (args,) if not supported
    try:
        return handler(args, context)
    except TypeError:
        return handler(args)


def execute(command: str, args: Dict[str, Any], timeout: Optional[float] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if command not in _registry:
        raise KeyError(f'unknown command: {command}')
    handler, desc, schema = _registry[command]

    # basic arg validation: check required keys and simple type hints in schema if provided
    if schema and isinstance(schema, dict):
        for k, tname in schema.items():
            if k not in args:
                raise ValueError(f'missing arg: {k}')
            # simple type enforcement
            if tname and args.get(k) is not None:
                if tname == 'int' and not isinstance(args.get(k), int):
                    raise ValueError(f'arg {k} must be int')
                if tname == 'str' and not isinstance(args.get(k), str):
                    raise ValueError(f'arg {k} must be str')

    to = timeout or DEFAULT_TIMEOUT
    # wrap handler to include context
    def _wrapped(a):
        return _call_handler(handler, a, context)

    res = _run_with_timeout(_wrapped, args, to)
    if res.get('timeout'):
        return {'ok': False, 'error': 'timeout', 'output': None}
    if 'error' in res:
        return {'ok': False, 'error': res['error'], 'output': None}

    val = res.get('value')
    out_str = None
    if isinstance(val, (str, int, float, bool)):
        out_str = str(val)
    else:
        try:
            import json
            out_str = json.dumps(val, ensure_ascii=False, indent=2)
        except Exception:
            out_str = str(val)

    if out_str and len(out_str) > MAX_OUTPUT_CHARS:
        out_str = out_str[:MAX_OUTPUT_CHARS] + '...[truncated]'

    return {'ok': True, 'output': out_str, 'data': val}


# register built-in commands
def _cmd_echo(args: Dict[str, Any]):
    # echo expects 'text'
    return args.get('text', '')


def _cmd_health(args: Dict[str, Any]):
    return {
        'uptime_seconds': time.time() - _started_at,
        'time': time.time(),
        'status': 'ok'
    }


register_command('echo', _cmd_echo, description='Echo text back', args_schema={'text': 'str'})
register_command('health', _cmd_health, description='Service health', args_schema={})

# Try to auto-import `commands` package so individual command modules (hello, etc.)
# can register themselves when present.
try:
    from . import commands  # type: ignore
except Exception:
    # not critical; commands may not exist in some test environments
    pass

# help command: list available commands with descriptions
def _cmd_help(args: Dict[str, Any]):
    # optional 'name' to show detailed info for a single command
    name = args.get('name') if isinstance(args, dict) else None
    cmds = list_commands()
    if name:
        for c in cmds:
            if c.get('name') == name:
                # return a detailed string for a single command
                schema = c.get('args_schema')
                s = f"{c.get('name')}: {c.get('description') or ''}"
                if schema:
                    s += f" (args: {schema})"
                return s
        raise KeyError(f'unknown command: {name}')

    # build a two-column textual table: name (left) | description (right)
    rows = []
    max_name = 0
    for c in cmds:
        nm = c.get('name') or ''
        if len(nm) > max_name:
            max_name = len(nm)
    for c in cmds:
        nm = c.get('name') or ''
        desc = c.get('description') or ''
        rows.append(f"{nm.ljust(max_name)}  {desc}")
    return "\n".join(rows)


register_command('help', _cmd_help, description='List available CLI commands (or help name=cmd)', args_schema={})
