from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import json

router = APIRouter()


def _repo_backend_dir() -> Path:
    # backend/app/api/v1/settings.py -> parents[3] == backend/
    return Path(__file__).resolve().parents[3]


def _read_json_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(str(path))
    text = path.read_text(encoding='utf-8')
    return json.loads(text)


def _write_json_file(path: Path, obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    path.write_text(text, encoding='utf-8')


@router.get('/easyberry')
async def get_easyberry():
    root = _repo_backend_dir()
    p = root / 'easyberry_config.json'
    try:
        data = _read_json_file(p)
        return JSONResponse(content=data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='easyberry_config.json not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/easyberry')
async def save_easyberry(req: Request):
    root = _repo_backend_dir()
    p = root / 'easyberry_config.json'
    body = await req.json()
    try:
        _write_json_file(p, body)
        # attempt to reload saved config into the in-memory easyberry database
        try:
            from app.modules.sw.easyberry.loader import load_from_file
            load_from_file(str(p))
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Failed reloading easyberry_config.json after save")
        return JSONResponse(content={'saved': True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/easyberry/reload')
async def reload_easyberry():
    """Reload `easyberry_config.json` from disk into the in-memory database."""
    root = _repo_backend_dir()
    p = root / 'easyberry_config.json'
    if not p.exists():
        raise HTTPException(status_code=404, detail='easyberry_config.json not found')
    try:
        from app.modules.sw.easyberry.loader import load_from_file
        load_from_file(str(p))
        return JSONResponse(content={'reloaded': True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/polling')
async def get_polling():
    root = _repo_backend_dir()
    p = root / 'polling_config.json'
    try:
        data = _read_json_file(p)
        return JSONResponse(content=data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='polling_config.json not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/polling')
async def save_polling(req: Request):
    root = _repo_backend_dir()
    p = root / 'polling_config.json'
    body = await req.json()
    try:
        _write_json_file(p, body)
        return JSONResponse(content={'saved': True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
