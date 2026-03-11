#!/usr/bin/env bash
set -euo pipefail

echo "[1/5] Checking Python dependencies..."
python3 -c "import fastapi, sqlalchemy, alembic, celery" >/dev/null

echo "[2/5] Applying migrations..."
alembic upgrade head

echo "[3/5] Running API health check..."
if command -v curl >/dev/null 2>&1; then
  curl -fsS "http://127.0.0.1:8000/healthz" >/dev/null
else
  echo "curl not found; skipping health probe"
fi

echo "[4/5] Validating Celery import path..."
python3 -c "from app.tasks.worker import celery_app; print(celery_app.main)" >/dev/null

echo "[5/5] Running tests..."
python3 -m pytest -q

echo "Smoke check passed."
