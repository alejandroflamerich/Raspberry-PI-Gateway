FROM python:3.11-slim

WORKDIR /app

# copiar el código
COPY . /app

# add entrypoint to ensure config files exist when container starts
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# instalar herramientas de compilación y dependencias de librerías nativas
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	   build-essential \
	   gcc \
	   libffi-dev \
	   libssl-dev \
	   python3-dev \
	&& rm -rf /var/lib/apt/lists/*

# instalar dependencias Python (incluye cryptography)
RUN pip install --no-cache-dir fastapi uvicorn gunicorn PyJWT python-dotenv pydantic-settings httpx cryptography

EXPOSE 8000

# Ejecutar Gunicorn con workers Uvicorn (producción)
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]
