# Phase 8 — Scaling, observability, CI/CD

> **Parent index:** [00-INDEX.md](00-INDEX.md)  
> **Depends on:** [08-phase-7-public-service.md](08-phase-7-public-service.md)  
> **Vision:** [`../Initial_idea.md`](../Initial_idea.md) — Phase 8  
> **Earlier phases:** [01](01-phase-0-repo-and-dev-env.md) → [07](07-phase-6-celery-redis.md)

## Objective

Prepare the platform for public load: multiple API/worker instances, monitoring, automated tests/deploy, and a path to Kubernetes — without pretending Day-1 needs K8s.

---

## Task checklist

### Task 8.1 — Horizontal API & workers

- [ ] Stateless FastAPI (sessions in JWT/Redis only)
- [ ] Multiple worker replicas on separate queues if needed (`html_to_pdf` vs `pdf_to_html`)
- [ ] Shared Redis + Postgres + object storage
- [ ] Document compose `scale worker=3` for local stress

### Task 8.2 — Load balancer / reverse proxy

- [ ] Nginx or cloud LB in front of API
- [ ] Health checks use `/health` (and later `/ready` including DB/Redis)

### Task 8.3 — CI with GitHub Actions

- [ ] On PR: ruff, pytest (backend), frontend typecheck/build
- [ ] Optional: build Docker images
- [ ] Cache pip/npm
- [ ] Do not publish secrets; use GH secrets for deploy later

### Task 8.4 — Observability

- [ ] Structured logs with `request_id` / `job_id`
- [ ] Metrics: conversion count, latency, queue depth, failure rate (Prometheus)
- [ ] Grafana dashboards (later)
- [ ] OpenTelemetry traces for API → broker → worker (later)

### Task 8.5 — Readiness & graceful shutdown

- [ ] `/ready` checks DB + Redis
- [ ] Celery warm shutdown; do not ack jobs mid-convert carelessly

### Task 8.6 — AWS deploy path (initial production)

- [ ] Containerize API + worker
- [ ] Managed Postgres + Redis (or ElastiCache) + S3
- [ ] Document minimal deploy (ECS/Fargate or single VM + compose) before K8s

### Task 8.7 — Kubernetes later

Only after pain with VM/compose:

- [ ] Deployments for API & workers
- [ ] HPA on CPU/queue depth
- [ ] Separate worker pools
- [ ] Secrets via K8s secrets / external secrets operator

### Task 8.8 — Portfolio narrative

- [ ] Update root `README.md` with architecture evolution story (why each piece was added)
- [ ] Link to `plans/` and `Initial_idea.md`
- [ ] Screenshots of UI + OpenAPI

---

## Acceptance criteria

- [ ] CI green on main flows
- [ ] Can run ≥2 API and ≥2 worker processes against one Redis/Postgres
- [ ] Basic metrics or structured logs sufficient to debug failed jobs
- [ ] Deploy docs exist for at least one production-ish path

## Out of scope / defer forever until needed

- Multi-region active-active
- Custom autoscaler algorithms
- Replacing WeasyPrint/PyMuPDF without product need

---

## Full plan chain (for agents)

1. [00-INDEX.md](00-INDEX.md)  
2. [01-phase-0-repo-and-dev-env.md](01-phase-0-repo-and-dev-env.md) — **venv + Docker**  
3. [02-phase-1-backend-foundation.md](02-phase-1-backend-foundation.md)  
4. [03-phase-2-html-to-pdf.md](03-phase-2-html-to-pdf.md)  
5. [04-phase-3-pdf-to-html.md](04-phase-3-pdf-to-html.md)  
6. [05-phase-4-frontend.md](05-phase-4-frontend.md)  
7. [06-phase-5-database.md](06-phase-5-database.md)  
8. [07-phase-6-celery-redis.md](07-phase-6-celery-redis.md)  
9. [08-phase-7-public-service.md](08-phase-7-public-service.md)  
10. [09-phase-8-scaling-observability.md](09-phase-8-scaling-observability.md) ← you are here  

**Implementation order for the next coding session:** start at Phase 0 and tick the status table in [00-INDEX.md](00-INDEX.md).

---

**Previous:** [08-phase-7-public-service.md](08-phase-7-public-service.md)  
**Back to index:** [00-INDEX.md](00-INDEX.md)
