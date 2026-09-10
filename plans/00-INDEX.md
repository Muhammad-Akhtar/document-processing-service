# Document Processing Service — Implementation Plans Index

> **Start here.** This is the master map for Cursor agents and humans.
> Source of truth for product vision: [`../Initial_idea.md`](../Initial_idea.md)

## Goal

Build a **document processing platform with pluggable converters** (not a one-off HTML↔PDF website), progressing from a working local FastAPI + converters product to Redis/Celery, PostgreSQL, React UI, then optional S3/AWS/Kubernetes.

## Dual local setup (required)

| Mode | Purpose |
|------|---------|
| **Python venv** | Primary path for day-to-day debugging of FastAPI, converters, pytest |
| **Docker Compose** | Postgres, Redis, workers, and “works like prod” runs |

Both are planned from Phase 0. Prefer **venv for backend API/converter debugging**; use Docker for dependencies and full-stack smoke tests.

## Repository layout (target)

```text
document-processing-service/          # this monorepo (or sibling repos later)
├── Initial_idea.md
├── plans/                            # ← you are here
├── backend/                          # FastAPI (document-platform-backend)
│   ├── .venv/                        # local virtualenv (gitignored)
│   ├── app/
│   │   ├── api/
│   │   ├── converters/
│   │   ├── storage/
│   │   ├── database/
│   │   ├── models/
│   │   └── workers/
│   ├── tests/
│   ├── requirements.txt / pyproject.toml
│   └── Dockerfile
├── frontend/                         # React + TypeScript
├── docker-compose.yml
├── storage/                          # local file storage (dev; S3 later)
└── README.md
```

> Note: `Initial_idea.md` names sibling GitHub repos (`document-platform-frontend` / `document-platform-backend`). **For this workspace we use a monorepo** (`backend/` + `frontend/`) unless you later split remotes. Plans assume monorepo paths.

## Plan documents (read in order)

| # | File | Phase | What it covers |
|---|------|-------|----------------|
| 00 | [00-INDEX.md](00-INDEX.md) | — | This index |
| 01 | [01-phase-0-repo-and-dev-env.md](01-phase-0-repo-and-dev-env.md) | Phase 0 | Repo skeleton, **venv**, Docker, tooling, security baseline notes |
| 02 | [02-phase-1-backend-foundation.md](02-phase-1-backend-foundation.md) | Phase 1 | FastAPI, Pydantic, upload, validation, local storage, viewers APIs |
| 03 | [03-phase-2-html-to-pdf.md](03-phase-2-html-to-pdf.md) | Phase 2 | WeasyPrint converter, CSS/images/fonts, download |
| 04 | [04-phase-3-pdf-to-html.md](04-phase-3-pdf-to-html.md) | Phase 3 | PyMuPDF extraction, limited layout reconstruction |
| 05 | [05-phase-4-frontend.md](05-phase-4-frontend.md) | Phase 4 | React + TS UI: upload, preview, convert, history |
| 06 | [06-phase-5-database.md](06-phase-5-database.md) | Phase 5 | PostgreSQL, users/docs/jobs history |
| 07 | [07-phase-6-celery-redis.md](07-phase-6-celery-redis.md) | Phase 6 | Async jobs, states, retries, progress |
| 08 | [08-phase-7-public-service.md](08-phase-7-public-service.md) | Phase 7 | Auth, rate limits, quotas, S3 later, hardening |
| 09 | [09-phase-8-scaling-observability.md](09-phase-8-scaling-observability.md) | Phase 8 | HA, monitoring, extended CI/CD, K8s later |
| 10 | [10-testing-and-ci.md](10-testing-and-ci.md) | Cross-cutting | Unit tests every phase; GitHub Actions CI; push to **`master`** after each phase |

## How agents should use these plans

1. Open **this index**, then the **next unfinished phase** file.
2. Complete tasks in order; check each **Acceptance criteria** before advancing.
3. Follow **Next plan** at the bottom of each phase file.
4. Do **not** skip security controls listed in Phase 0/7 when adding upload/conversion features.
5. Prefer implementing **converter plugins** behind a shared `Converter` interface (see Phase 1–2).
6. Keep conversion **out of FastAPI route bodies** once Phase 6 lands; until then sync conversion is OK behind a service layer.
7. Add **unit/API tests for every new case** in the phase; keep [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) green. See [10-testing-and-ci.md](10-testing-and-ci.md).
8. After each phase completes: commit and **`git push origin master`**.

## Progressive build rule

```text
FastAPI + venv + local storage + WeasyPrint + PyMuPDF
        → React UI
        → PostgreSQL
        → Redis + Celery
        → Auth / quotas / S3
        → Scale / observe
```

Do not introduce Kubernetes, OpenTelemetry, or S3 on day one.

## Status tracker (update as you go)

| Phase | Status | Notes |
|-------|--------|-------|
| 0 Repo & dev env | Done | Skeleton, venv (3.13), health, Docker stubs, CI + test conventions |
| Testing & CI baseline | Done | `ci.yml` on `master`; see plan 10 |
| 1 Backend foundation | Not started | |
| 2 HTML → PDF | Not started | |
| 3 PDF → HTML | Not started | |
| 4 Frontend | Not started | |
| 5 Database | Not started | |
| 6 Celery / Redis | Not started | |
| 7 Public service | Not started | |
| 8 Scaling / observability | Not started | |

## Cross-cutting references

- Architecture diagram & stack: [`../Initial_idea.md`](../Initial_idea.md) (sections: recommended stack, architecture, security)
- Converter plugin layout: `backend/app/converters/` (`base.py`, `html_to_pdf.py`, `pdf_to_html.py`, …)
- Local files first; S3 deferred: Phase 7 and `Initial_idea.md` note near the end
- Tests & CI: [10-testing-and-ci.md](10-testing-and-ci.md) — required from Phase 0 onward
- Default git branch: **`master`**

---

**Next:** [02-phase-1-backend-foundation.md](02-phase-1-backend-foundation.md)
