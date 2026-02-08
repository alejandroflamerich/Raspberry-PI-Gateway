from ..registry import register_command
from typing import Dict, Any


def handler(args: Dict[str, Any], context=None):
    try:
        from app.modules.sw.modbus import polling as polling_mod
    except Exception as e:
        raise RuntimeError(f'failed importing polling module: {e}')

    pollers = getattr(polling_mod, '_example_pollers', None)
    if not pollers:
        return []

    out = []
    for p in (pollers or []):
        try:
            name = getattr(p, 'name', None)
            pid = getattr(p, '_poller_id', None)
            interval = getattr(p, 'interval', None)
            alive = getattr(p, 'is_alive', lambda: False)()
            stopped = getattr(p, 'stopped', lambda: True)()
            out.append({
                'name': name,
                'poller_id': pid,
                'interval': float(interval) if interval is not None else None,
                'alive': bool(alive),
                'stopped': bool(stopped),
            })
        except Exception:
            out.append({'error': 'failed reading poller info'})

    return out


register_command('pollers', handler, description='List active pollers and their configured interval', args_schema={})
