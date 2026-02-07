Backend (FastAPI) - quickstart

1) Create venv and activate (PowerShell):
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
2) Install dependencies:
   pip install fastapi uvicorn PyJWT python-dotenv
3) From this folder run:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Endpoints:
- GET /api/v1/health
- POST /api/v1/auth/login
- GET /api/v1/points/  (requires Bearer token)
