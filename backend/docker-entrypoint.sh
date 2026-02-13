#!/bin/sh
set -e

echo "[entrypoint] checking configuration files..."

# Copy .env from example if missing
if [ ! -f /app/.env ] && [ -f /app/.env.example ]; then
  echo "[entrypoint] .env not found — copying .env.example -> .env"
  cp /app/.env.example /app/.env
fi

# Ensure backend easyberry config exists
if [ ! -f /app/backend/easyberry_config.json ] && [ -f /app/backend/easyberry_config.example.json ]; then
  echo "[entrypoint] backend/easyberry_config.json not found — copying example"
  cp /app/backend/easyberry_config.example.json /app/backend/easyberry_config.json
fi

# Ensure polling_config exists (if present as example)
if [ ! -f /app/polling_config.json ] && [ -f /app/polling_config.example.json ]; then
  echo "[entrypoint] polling_config.json not found — copying example"
  cp /app/polling_config.example.json /app/polling_config.json
fi

echo "[entrypoint] config check complete"

# Exec the given command (defaults to Gunicorn via CMD)
exec "$@"
