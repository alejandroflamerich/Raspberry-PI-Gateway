from ..registry import register_command
from typing import Dict, Any


def handler(args: Dict[str, Any], context=None):
    try:
        from app.modules.sw.easyberry.packet_store import eb_packet_store
    except Exception as e:
        raise RuntimeError(f'failed accessing packet store: {e}')

    items = eb_packet_store.get_last(limit=1)
    if not items:
        return {'error': 'no packets recorded'}

    it = items[-1]

    out = {
        'ts': float(it.get('ts')) if it.get('ts') is not None else None,
        'endpoint': it.get('endpoint'),
        'request': it.get('request'),
        'request_headers': it.get('request_headers'),
        'response': it.get('response'),
        'response_headers': it.get('response_headers'),
        'status': it.get('status'),
        'content_type': it.get('content_type'),
        'note': it.get('note'),
    }
    return out


register_command('last-req', handler, description='Show last Easyberry request including headers', args_schema={})
