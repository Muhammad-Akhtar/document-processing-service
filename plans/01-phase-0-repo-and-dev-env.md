# Phase 0 — Repository skeleton & developer environment

> **Parent index:** [00-INDEX.md](00-INDEX.md)  
> **Source vision:** [`../Initial_idea.md`](../Initial_idea.md)  
> **Next:** [02-phase-1-backend-foundation.md](02-phase-1-backend-foundation.md)

## Objective

Create a clean monorepo, **local Python virtualenv for backend debugging**, Docker Compose for optional infra, and baseline docs/ignores so later phases have a predictable layout.

## Why this phase exists

You will debug converters and FastAPI frequently. A **venv** avoids polluting system Python and works without spinning Docker for every code change. Docker remains for Postgres/Redis/workers when those arrive.

---

## Prerequisites

- [x] Python **3.12+** (prefer 3.12 or 3.13) installed on Windows
- [ ] Git installed *(workspace not a git repo yet — init when you want)*
- [ ] Docker Desktop available (optional until Phase 5–6, but scaffold now)
- [ ] Node.js 20+ (needed later for Phase 4; can install anytime)
- [x] Read [`../Initial_idea.md`](../Initial_idea.md) once for architecture context

---

## Task checklist

### Task 0.1 — Confirm workspace root

- [x] Work inside `document-processing-service/`
- [x] Keep `Initial_idea.md` and `plans/` at repo root
- [ ] Initialize git if not already (`git init`) — only if user wants; do not force remotes

### Task 0.2 — Create directory skeleton

Create:

```text
backend/
  app/
    __init__.py
    api/
    converters/
    storage/
    database/
    models/
    workers/
    core/           # settings, logging, security helpers
  tests/
  scripts/
frontend/           # empty placeholder + README until Phase 4
storage/
  uploads/
  outputs/
  previews/
plans/              # already exists
```

- [x] Add `backend/app/**/__init__.py` where needed so packages import cleanly
- [x] Add `.gitkeep` under `storage/uploads`, `storage/outputs`, `storage/previews`
- [x] Add `frontend/README.md` pointing to Phase 4 plan

### Task 0.3 — Create Python virtual environment (required)

From repo root (PowerShell):

```powershell
cd backend
py -3.12 -m venv .venv
# If py launcher fails, use: python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

- [x] Create `backend/.venv`
- [x] Activate and verify: `python --version` shows 3.12+ *(3.13.9)*
- [x] Ensure `.venv/` is in `.gitignore`

**Agent note:** Always activate this venv before `pip install`, `uvicorn`, or `pytest` during local debugging.

### Task 0.4 — Dependency manifests (minimal bootstrap)

Create `backend/requirements.txt` (or `pyproject.toml` — prefer one style and stick to it; start with `requirements.txt` + optional `requirements-dev.txt`):

**Runtime (Phase 0–2 starter set):**

```text
fastapi
uvicorn[standard]
python-multipart
pydantic
pydantic-settings
# converters added in Phase 2–3:
# weasyprint
# pymupdf
# beautifulsoup4
# lxml
```

**Dev:**

```text
pytest
pytest-asyncio
httpx
ruff
```

- [x] Install into venv: `pip install -r requirements.txt -r requirements-dev.txt`
- [x] Freeze optional: `pip freeze > requirements.lock.txt` (or document `pip-compile` later)

**Windows + WeasyPrint note (Phase 2):** WeasyPrint needs GTK/Pango/Cairo libs. Document install steps in `backend/README.md` (MSYS2 or WeasyPrint Windows docs). Docker image can carry those libs for CI.

### Task 0.5 — Backend README + settings stub

- [x] Write `backend/README.md`: how to activate venv, run API, run tests, Docker alternative
- [x] Add `backend/app/core/config.py` stub with `pydantic-settings` (e.g. `STORAGE_ROOT`, `MAX_UPLOAD_BYTES`, `CORS_ORIGINS`)
- [x] Add `backend/.env.example` (no secrets): local paths, debug flags
- [x] Add `backend/.env` to `.gitignore`

### Task 0.6 — Root `.gitignore`

Ignore at minimum:

```text
.venv/
__pycache__/
*.pyc
.env
.mypy_cache/
.pytest_cache/
.ruff_cache/
node_modules/
dist/
build/
storage/uploads/*
storage/outputs/*
storage/previews/*
!storage/**/.gitkeep
*.pdf
!tests/fixtures/**
```

### Task 0.7 — Docker scaffold (compose ready, not mandatory to run yet)

- [x] `backend/Dockerfile` (Python slim; later extend for WeasyPrint system deps)
- [x] Root `docker-compose.yml` with services placeholders:
  - `api` (build backend)
  - `postgres` (commented or profile `full` until Phase 5)
  - `redis` (Phase 6)
  - `worker` (Phase 6)
- [x] Document: **local venv for API debug**; **compose for integrated stack**

Example mental model:

```text
Day-to-day:  .venv + uvicorn --reload
Full stack:  docker compose up
```

### Task 0.8 — Security baseline (design only; implement checks in Phase 1+)

Capture in `backend/README.md` or `docs/SECURITY.md`:

- [x] File size limits
- [x] MIME + extension validation
- [x] No arbitrary filesystem reads in converters
- [x] HTML conversion: no SSRF / no local file URLs / no JS execution
- [x] Sandboxed workers later (Phase 7)
- [x] Local storage under project `storage/` with secure serve (no path traversal)

Do **not** implement full malware scanning yet.

### Task 0.9 — Smoke “hello” app (optional but recommended)

- [x] Minimal FastAPI app: `GET /health` → `{"status":"ok"}`
- [x] Run via venv: `uvicorn app.main:app --reload --app-dir backend` (adjust module path to match layout)
- [x] Confirm OpenAPI at `/docs`

---

## Recommended backend package layout after Phase 0

```text
backend/
  .venv/
  app/
    main.py
    core/
      config.py
    api/
    converters/
    storage/
    database/
    models/
    workers/
  tests/
  requirements.txt
  requirements-dev.txt
  Dockerfile
  README.md
  .env.example
```

---

## Acceptance criteria

- [x] Directory skeleton exists as above
- [x] `backend/.venv` created and documented
- [x] Dependencies install into venv without error (core set)
- [x] `.gitignore` excludes venv, env files, and uploaded blobs
- [x] `GET /health` works from activated venv (if Task 0.9 done)
- [x] Dockerfiles/compose exist as stubs even if unused daily
- [x] Agent can find next steps via [02-phase-1-backend-foundation.md](02-phase-1-backend-foundation.md)

## Out of scope

- Real converters, React app, Postgres, Celery, S3, auth

## Risks / notes

| Risk | Mitigation |
|------|------------|
| WeasyPrint native deps on Windows | Document MSYS2; offer Docker path for conversion tests |
| Monorepo vs two GitHub repos | Stay monorepo until split is needed; keep folder names clear |
| Accidental commit of uploads | Strict gitignore + size limits |

---

**Previous:** [00-INDEX.md](00-INDEX.md)  
**Next:** [02-phase-1-backend-foundation.md](02-phase-1-backend-foundation.md)
