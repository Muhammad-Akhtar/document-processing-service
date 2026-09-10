# Phase 6 — Production processing (Redis + Celery)

> **Parent index:** [00-INDEX.md](00-INDEX.md)  
> **Depends on:** [06-phase-5-database.md](06-phase-5-database.md)  
> **Next:** [08-phase-7-public-service.md](08-phase-7-public-service.md)  
> **Vision:** [`../Initial_idea.md`](../Initial_idea.md) — Phase 6 tasks 32–39

## Objective

Move heavy conversion off the API process onto **Celery workers** backed by **Redis**, with job states, retries, failure handling, and progress tracking. FastAPI validates, stores, enqueues, and returns `job_id`.

## Target flow

```text
FastAPI → create job (DB) → enqueue Celery → return job_id
                ↓
             Redis broker
                ↓
          Celery worker → Converter → storage + DB update
```

---

## Prerequisites

- [ ] Conversion service + DB job model exist
- [ ] Docker for Redis (recommended) while API/worker may use venv

---

## Task checklist

### Task 6.1 — Redis

- [ ] Add `redis` service to compose
- [ ] Config: `REDIS_URL`
- [ ] Healthcheck; document `docker compose up redis -d`

### Task 6.2 — Celery app

- [ ] `app/workers/celery_app.py`
- [ ] Broker + result backend (Redis)
- [ ] Packaging so worker imports `app.converters` correctly
- [ ] Document worker start:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
celery -A app.workers.celery_app worker --loglevel=INFO
```

### Task 6.3 — Background conversion task

- [ ] Task `run_conversion(job_id: str)`
- [ ] Load job + source path from DB
- [ ] Run registry converter
- [ ] Save output, link `output_document_id`, set status `completed`
- [ ] On exception: status `failed`, store safe error message

### Task 6.4 — API changes

- [ ] `POST /api/v1/conversions` returns `202` + `job_id` (breaking change from sync — update frontend)
- [ ] `GET /api/v1/jobs/{job_id}` → status, progress, result document id, error
- [ ] Remove long-running work from request thread

### Task 6.5 — Job states

States: `pending` → `processing` → `completed` | `failed`

- [ ] Enforce valid transitions in one place
- [ ] Idempotency considerations if task retried

### Task 6.6 — Retry & failure handling

- [ ] Celery autoretry for transient errors (optional, capped)
- [ ] Do not infinite-retry corrupt documents
- [ ] Timeout soft/hard limits for huge files

### Task 6.7 — Dead-letter strategy

- [ ] After max retries: mark failed; optional DLQ queue or `dead_letter` flag in DB
- [ ] Document how to inspect failed jobs

### Task 6.8 — Progress tracking

- [ ] Simple progress: 0 → 50 (started) → 100 (done); or page-based for PDF→HTML
- [ ] Store progress on job row or Redis key; expose via job GET
- [ ] Frontend polls every N ms with backoff

### Task 6.9 — Frontend updates

- [ ] Convert action polls job until terminal state
- [ ] Show progress indicator bound to job progress
- [ ] Handle failure messages

### Task 6.10 — Compose worker service

- [ ] `worker` service builds same backend image, runs celery
- [ ] Local debug alternative: API in venv + worker in venv + Redis in Docker

### Task 6.11 — Tests

- [ ] Unit-test task with eager Celery mode (`task_always_eager`) in pytest
- [ ] API returns 202 and job completes in eager mode

---

## Acceptance criteria

- [ ] Large conversion does not block uvicorn workers
- [ ] Job status visible via API; frontend polls successfully
- [ ] Retries/failures behave predictably
- [ ] Hybrid debug path documented (venv API + venv worker + Docker Redis)

## Out of scope

- Auth, rate limits, S3, K8s autoscaling

## Agent debugging tip

If conversion “hangs” at pending, check: Redis up? Worker running? Same `REDIS_URL`? Task module imported?

---

**Previous:** [06-phase-5-database.md](06-phase-5-database.md)  
**Next:** [08-phase-7-public-service.md](08-phase-7-public-service.md)
