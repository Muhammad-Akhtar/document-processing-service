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
| 3+ | Follow [`plans/00-INDEX.md`](plans/00-INDEX.md) |

### Quick start (backend)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health: http://127.0.0.1:8000/health — details in [`backend/README.md`](backend/README.md).
