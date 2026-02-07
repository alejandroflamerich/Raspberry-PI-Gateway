from fastapi import APIRouter
from typing import Any, Dict
from app.modules.sw.easyberry.store import database
from app.modules.sw.modbus.polling import packet_store
from app.modules.sw.easyberry.packet_store import eb_packet_store
from app.modules.sw.modbus.polling import start_example_polling, stop_example_polling, example_polling_status

router = APIRouter()


@router.get("/database")
async def get_database() -> Dict[str, Any]:
    """Return a JSON-serializable snapshot of the in-memory Easyberry database."""
    pollers = database.get_pollers()
    mbid_index = {}
    for k, v in getattr(database, "mbid_index", {}).items():
        pid, thing = v
        mbid_index[k] = {"poller_id": pid, "thing": thing}
    return {"pollers": pollers, "mbid_index": mbid_index}


@router.get("/packets")
async def get_packets(limit: int = 200):
    """Return recent packet exchanges logged by pollers."""
    items = packet_store.get_last(limit=limit)
    import datetime
    out = []
    for it in items:
        ts = datetime.datetime.fromtimestamp(it['ts']).strftime('%Y-%m-%d %H:%M:%S')
        out.append({
            'ts': ts,
            'poller_id': it.get('poller_id'),
            'status': it.get('status'),
            'request': it.get('request'),
            'response': it.get('response'),
            'note': it.get('note'),
        })
    return {'packets': out}


@router.get("/easyberry")
async def get_easyberry_packets(limit: int = 200):
    """Return recent HTTP exchanges recorded with easyberry server."""
    items = eb_packet_store.get_last(limit=limit)
    import datetime
    out = []
    for it in items:
        ts = datetime.datetime.fromtimestamp(it['ts']).strftime('%Y-%m-%d %H:%M:%S')
        out.append({
            'ts': ts,
            'endpoint': it.get('endpoint'),
                'status': it.get('status'),
                'content_type': it.get('content_type'),
                'request': it.get('request'),
                'response': it.get('response'),
            'note': it.get('note'),
        })
    return {'easyberry': out}


@router.post('/packets/clear')
async def clear_packets():
    """Clear the in-memory packet store."""
    try:
        packet_store.clear()
        return {'cleared': True}
    except Exception as e:
        return {'cleared': False, 'error': str(e)}


@router.post('/polling/start')
async def api_start_polling():
    ok = start_example_polling()
    if not ok:
        return {'started': False, 'detail': 'already running'}
    return {'started': True}


@router.post('/polling/stop')
async def api_stop_polling():
    ok = stop_example_polling()
    if not ok:
        return {'stopped': False, 'detail': 'not running'}
    return {'stopped': True}


@router.get('/polling/status')
async def api_polling_status():
    return {'running': bool(example_polling_status())}
