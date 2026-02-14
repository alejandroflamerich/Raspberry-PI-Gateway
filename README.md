# Edge Project - Scaffold

This repository contains a minimal scaffold for an edge application (FastAPI backend + React + Vite frontend).

Quick plan of what to do next (Windows PowerShell):

1) Backend
- Create and activate venv
  ```powershell
  cd backend
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install fastapi uvicorn PyJWT python-dotenv
  ```
- Run server
  ```powershell
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

2) Frontend
  ```powershell
  cd frontend
  npm install
  npm run dev
  ```

Checks:
- GET http://localhost:8000/api/v1/health
- Frontend: http://localhost:5173

Explainer video
- https://youtu.be/NhdJfKgNIPw
