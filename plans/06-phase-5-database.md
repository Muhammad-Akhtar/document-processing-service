# Phase 5 — Database (PostgreSQL)

> **Parent index:** [00-INDEX.md](00-INDEX.md)  
> **Depends on:** [05-phase-4-frontend.md](05-phase-4-frontend.md) (UI can remain; history moves server-side)  
> **Next:** [07-phase-6-celery-redis.md](07-phase-6-celery-redis.md)  
> **Vision:** [`../Initial_idea.md`](../Initial_idea.md) — Phase 5 tasks 27–31

## Objective

Introduce PostgreSQL for durable metadata: users (optional stub), documents, conversion jobs, and history. Files stay on **local disk** (`storage/`); DB stores paths and metadata. S3 comes later (Phase 7).

## Prerequisites

- [ ] Phases 1–3 APIs exist
- [ ] Docker available for Postgres **or** local Postgres install
- [ ] Venv activated for backend

---

## Task checklist

### Task 5.1 — Postgres in Compose

- [ ] Enable `postgres` service in `docker-compose.yml`
- [ ] Volume for data persistence
- [ ] Connection URL in `backend/.env.example`: `DATABASE_URL=postgresql+asyncpg://...` (or sync SQLAlchemy URL — pick one style)
- [ ] Document: run Postgres via Docker even when API runs in venv

### Task 5.2 — ORM / migrations

- [ ] Add SQLAlchemy 2.x (+ Alembic)
- [ ] Prefer async SQLAlchemy if FastAPI routes are async; keep consistency
- [ ] Initial Alembic migration

### Task 5.3 — Schema: users (minimal)

Even before full auth (Phase 7):

- [ ] `users` table: id, email (nullable unique), created_at
- [ ] Optional anonymous user / null `owner_id` for local-only mode
- [ ] Do not build full auth yet — just FK readiness

### Task 5.4 — Schema: documents

- [ ] id (UUID), owner_id nullable, original_filename, content_type, size_bytes
- [ ] storage_backend (`local` now; `s3` later), storage_key/path
- [ ] checksum optional, created_at, deleted_at soft-delete optional

### Task 5.5 — Schema: conversion_jobs

- [ ] id, source_document_id, output_document_id nullable
- [ ] source_format, target_format
- [ ] status: pending/processing/completed/failed
- [ ] error_message, created_at, started_at, finished_at
- [ ] For Phase 5 (still sync): create job row, run convert, update row in one request
- [ ] Prepares Phase 6 async workers

### Task 5.6 — Schema: conversion history views

- [ ] List endpoint `GET /api/v1/conversions` or `/history` with filters
- [ ] Replace frontend localStorage history with API-backed list when available

### Task 5.7 — Repository layer

- [ ] `app/database/` session dependency
- [ ] Repositories/services for Document + Job CRUD
- [ ] Migrate Phase 1 JSON sidecars → DB writes (keep files on disk)

### Task 5.8 — Tests

- [ ] Use pytest with test DB or SQLite only if dialect-compatible; prefer Postgres test container / compose profile `test`
- [ ] CRUD + conversion job status updates

### Task 5.9 — Frontend wiring

- [ ] Point history panel at server API
- [ ] Show job status from DB

---

## Suggested tables (summary)

```text
users
documents
conversion_jobs
```

Keep schema boring and indexed on `owner_id`, `created_at`, `status`.

---

## Acceptance criteria

- [ ] Postgres runs via Docker; API in venv connects successfully
- [ ] Uploads and conversions persist metadata in DB
- [ ] History survives API restart
- [ ] Alembic migrations apply cleanly on empty DB
- [ ] Local files still under `storage/` (no S3 yet)

## Out of scope

- Redis/Celery (Phase 6)
- Real authentication (Phase 7)
- S3

## Hybrid debug workflow (agents)

```text
docker compose up postgres -d
cd backend && .\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn ...
```

---

**Previous:** [05-phase-4-frontend.md](05-phase-4-frontend.md)  
**Next:** [07-phase-6-celery-redis.md](07-phase-6-celery-redis.md)
