# Next.js + FastAPI Monorepo

A social app built as a monorepo: a Next.js web client, a FastAPI service, and the infrastructure to run both locally with one command.

![Next.js](https://img.shields.io/badge/Next.js-web-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-api-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Alembic-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-cache-DC382D?style=flat-square&logo=redis&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-object%20storage-C72E49?style=flat-square&logo=minio&logoColor=white)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)

## What is inside

| Path | What it is |
| --- | --- |
| `apps/web` | Next.js app, App Router, TypeScript |
| `apps/api` | FastAPI service with SQLAlchemy models and Alembic migrations |
| `packages/` | Shared UI primitives and shared configuration |
| `Dockerfile.api`, `Dockerfile.web` | Separate images, so each app builds and deploys on its own |
| `.github/workflows/ci.yml` | Continuous integration |

## Infrastructure

`docker compose` brings up three backing services:

| Service | Purpose | Local endpoint |
| --- | --- | --- |
| PostgreSQL | Application data | `postgresql://postgres:postgres@localhost:5432/app` |
| Redis | Caching and ephemeral state | `localhost:6379` |
| MinIO | S3-compatible object storage for uploads | console on `localhost:9001` |

Those credentials are throwaway values for local containers only. Deployments read everything from environment variables — copy the `.env.example` files and fill them in.

## Quick start

```bash
docker compose up -d postgres redis minio
docker compose -f docker-compose.yml -f docker-compose.override.yml up --build
```

Web on http://localhost:3000, API on http://localhost:8000, MinIO console on http://localhost:9001.

The override file runs both apps with hot reload, so this is the setup to develop against.

## Running without Docker

```bash
# API
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload

# Web
cd apps/web
npm install
npm run dev
```

## Database

Schema is managed with Alembic rather than created on startup, so every change is reviewable and reversible.

```bash
cd apps/api
alembic upgrade head          # apply migrations
alembic revision -m "desc"    # new migration after a model change
alembic downgrade -1          # roll back one
```

Seed sample data (50 users, 200 posts):

```bash
cd apps/api
python -m app.scripts.seed
```

## Tests and linting

```bash
pytest -q apps/api/tests      # API tests
ruff apps/api                 # Python lint
cd apps/web && npm run lint   # ESLint
```

## Requirements

Docker and Docker Compose. For non-Docker development, Node.js LTS and Python 3.11.
