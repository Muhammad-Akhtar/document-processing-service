# Document Processing Service

Pluggable document-processing platform (HTML ↔ PDF first), evolving toward a production service.

## Docs for implementation

| Doc | Purpose |
|-----|---------|
| [`Initial_idea.md`](Initial_idea.md) | Product vision, stack, architecture |
| [`plans/00-INDEX.md`](plans/00-INDEX.md) | **Start here for step-by-step implementation** |
| [`plans/10-testing-and-ci.md`](plans/10-testing-and-ci.md) | Unit tests every phase; CI; push to `master` |

Local backend debugging uses a **Python venv** (`backend/.venv`). Docker Compose is for Postgres/Redis/workers and prod-like runs. Details: [`plans/01-phase-0-repo-and-dev-env.md`](plans/01-phase-0-repo-and-dev-env.md).

Default branch is **`master`**. GitHub Actions runs on each push: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Status

| Phase | Status |
|-------|--------|
| 0 Repo & dev env | Done |
| Testing & CI baseline | Done (TDD required) |
| 1 Backend foundation | Done |
| 2 HTML → PDF | Done |
| 3 PDF → HTML | Done |
| 4 Frontend | Done |
| 5+ | Follow [`plans/00-INDEX.md`](plans/00-INDEX.md) |

## Quick start (Docker — recommended on Windows)

WeasyPrint needs Linux system libraries. On Windows, run **both** API and UI in Docker so HTML → PDF works without installing GTK.

From the repo root (Docker Desktop running):

```powershell
docker compose up --build
```

| Service | URL |
|---------|-----|
| UI (DocConvert) | http://127.0.0.1:5173 |
| API (direct) | http://127.0.0.1:8008 |
| API health | http://127.0.0.1:8008/health |
| OpenAPI docs | http://127.0.0.1:8008/docs |

The UI nginx proxies `/api` and `/health` to the `api` container, so use the **UI URL** for manual testing (upload → preview → convert → download).

Useful variants:

```powershell
docker compose up --build api          # API only on :8008
docker compose up --build api web      # same as default full stack
docker compose run --rm --build test   # full pytest in Linux (WeasyPrint included)
docker compose down                    # stop containers
```

Storage files land in `./storage` on the host.

## Quick start (local — venv + npm)

Use this for day-to-day code changes. On Windows, HTML → PDF may fail or skip without WeasyPrint native libs; use Docker for that path.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health: http://127.0.0.1:8000/health — details in [`backend/README.md`](backend/README.md).

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173 — details in [`frontend/README.md`](frontend/README.md).

### Hybrid (Docker API + local Vite)

Good when iterating on the UI but still need WeasyPrint:

```powershell
# terminal 1 — from repo root
docker compose up --build api

# terminal 2 — frontend
cd frontend
$env:VITE_PROXY_TARGET="http://127.0.0.1:8008"
npm run dev
```

Open http://127.0.0.1:5173 (Vite proxies `/api` to the Docker API on **8008**).
