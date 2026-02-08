FROM python:3.11-slim

WORKDIR /app

# copiar el código
COPY . /app

# instalar dependencias mínimas + gunicorn para producción
RUN pip install --no-cache-dir fastapi uvicorn gunicorn PyJWT python-dotenv pydantic-settings

EXPOSE 8000

# Ejecutar Gunicorn con workers Uvicorn (producción)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]
