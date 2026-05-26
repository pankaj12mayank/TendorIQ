#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting TenderIQ API on port ${PORT:-8000}..."
exec uvicorn src.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${WORKERS:-1}"
