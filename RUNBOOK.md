# Runbook

## Prerequisites
- Docker and Docker Compose
- Node.js LTS (for local web dev without Docker)
- Python 3.11 (for local API dev without Docker)

## Quick Start (Docker)
1. Start infra (DB/Redis/MinIO) and dev servers with hot reload:
   - `docker compose up -d postgres redis minio`
   - `docker compose -f docker-compose.yml -f docker-compose.override.yml up --build`
2. API: http://localhost:8000
3. Web: http://localhost:3000
4. MinIO: http://localhost:9001 (user/pass: minioadmin/minioadmin)

Copy `.env.example` files to `.env` where appropriate to configure.

## Local Dev (without Docker)
- API:
  - `cd apps/api`
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -e .`
  - `uvicorn app.main:app --reload`
- Web:
  - `cd apps/web`
  - `npm install`
  - `npm run dev`

## Database
- Postgres default connection (docker): `postgresql://postgres:postgres@localhost:5432/app`
- Create DB schema using Alembic:
  - Ensure env vars are set (see `.env.example`)
  - From `apps/api`: `alembic upgrade head`

## Migrations
- Create new migration after model changes:
  - `alembic revision -m "desc"`
  - Edit generated file under `apps/api/alembic/versions/`
  - `alembic upgrade head`

## Seeding
- Seed sample data (50 users, 200 posts):
  - `cd apps/api`
  - `python -m app.scripts.seed`

## Testing & Linting
- API tests: `pytest -q apps/api/tests`
- Ruff (Python lint): `ruff apps/api`
- ESLint (Web):
  - `cd apps/web && npm run lint`

## Common Commands
- Rebuild API image: `docker build -f Dockerfile.api .`
- Rebuild Web image: `docker build -f Dockerfile.web .`
- Tail API logs: `docker compose logs -f api`
- Create a new Next page: add file under `apps/web/src/app/<route>/page.tsx`
- Run Alembic downgrade: `alembic downgrade -1`

