from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings
from app.core.logging import configure_logging
from app.api.v1.router import api_router

configure_logging()

app = FastAPI(title="edge-service", version="0.1.0")

# For development convenience allow all origins when running in development mode.
# In production keep `settings.cors_origins` strictly configured.
if getattr(settings, "app_env", "development") == "development":
    allow_origins = ["*"]
else:
    allow_origins = [str(o) for o in settings.cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup_event():
    # place startup tasks here (connect db, hw init)
    # Load easyberry initial database if present so `GET /debug/database` returns data
    try:
        from pathlib import Path
        from app.modules.sw.easyberry.loader import load_from_file
        # `main.py` is located at backend/app/main.py; parents[1] == backend
        root = Path(__file__).resolve().parents[1]
        eb_path = root / 'easyberry_config.json'
        if eb_path.exists():
            try:
                load_from_file(str(eb_path))
            except Exception:
                # do not prevent startup on load errors; log and continue
                import logging
                logging.getLogger(__name__).exception("Failed loading easyberry_config.json at startup")
    except Exception:
        # ignore if easyberry module is not available
        import logging
        logging.getLogger(__name__).debug("easyberry loader not available at startup")
