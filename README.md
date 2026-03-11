# Cyber Incident Tracker

Monorepo for a SaaS platform that aggregates, normalizes, and surfaces cybersecurity incidents tied to organizations.

## Current Scope

- `backend`: FastAPI service, ingestion pipeline modules, and worker tasks.
- `frontend`: Next.js app scaffold.
- `docs`: product, taxonomy, source policy, and runbook documentation.
- `data`: seed/reference datasets.
- `infra`: local development and deployment support files.

## Quick Start

1. Copy `backend/.env.example` to `backend/.env`.
2. Start local dependencies:
   - `docker compose up -d`
3. Install backend dependencies and run migrations:
   - `cd backend && python -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
   - `alembic upgrade head`
4. Start backend:
   - `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
5. Start frontend:
   - `cd frontend && npm install && npm run dev`
   - Optional API URL override: copy `frontend/.env.local.example` to `frontend/.env.local`
6. Optional: start worker/beat:
   - `cd backend && source .venv/bin/activate && celery -A app.tasks.worker.celery_app worker --loglevel=info`
   - `cd backend && source .venv/bin/activate && celery -A app.tasks.worker.celery_app beat --loglevel=info`
7. Optional bulk vendor onboarding:
   - `POST /api/v1/vendors/import` to create many vendors from organizations in one request.
8. Optional no-terminal deployment mode:
   - Use systemd units in `infra/systemd/` (API, worker, beat, frontend).
   - Optional Nginx reverse proxy config in `infra/nginx/cyberincident.conf`.

## VPS Preflight

- Update `backend/.env` with production-safe values:
  - `ALLOWED_ORIGINS` for your frontend host(s)
  - `TRUSTED_HOSTS` for your API domain/IP
  - `SEC_USER_AGENT` with a real contact email (required best practice for SEC endpoints)
- Run smoke checks:
  - `cd backend && source .venv/bin/activate && bash scripts/smoke_check.sh`
- To avoid many open terminals in VPS environments, install the sample systemd units in `infra/systemd/`.
