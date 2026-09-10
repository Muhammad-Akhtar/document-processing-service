# Backend (FastAPI)

Document processing API. Phase 0 provides a health endpoint and project layout; converters and upload APIs arrive in later phases.

## Dual setup

| Mode | When to use |
|------|-------------|
| **Python venv** (this folder) | Day-to-day debugging of FastAPI, converters, pytest |
| **Docker Compose** (repo root) | Postgres/Redis/workers and prod-like runs |

Prefer the venv for API work. Do not require Docker for every code change.

## Prerequisites

- Python **3.12+** (3.13 OK)
- Optional: Docker Desktop for compose

## Virtualenv setup (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

Verify: `python --version` should show 3.12+.

Copy env example if you need overrides:

```powershell
Copy-Item .env.example .env
```

## Run the API

From `backend/` with venv activated:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Tests

```powershell
pytest
```

## Docker alternative

From repo root:

```powershell
docker compose up --build api
```

## WeasyPrint on Windows (Phase 2)

HTML → PDF needs GTK/Pango/Cairo. Options:

1. Follow [WeasyPrint — Windows](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows) (often via MSYS2 / GTK3 runtime).
2. Run conversion via Docker: `docker compose up --build api` (image installs Pango/Cairo).
3. CI installs the same system packages on Ubuntu; local Windows without native libs will **skip** WeasyPrint render tests automatically.

```powershell
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

## Conversions

```http
POST /api/v1/conversions
{"source_document_id": "<uuid>", "target_format": "pdf"}
```

Then download via the returned `download_url` (`GET /api/v1/documents/{output_id}/download`).

Remote `http(s)` assets in HTML are **blocked** (no SSRF); only files under the document directory are loaded.

## PDF → HTML (Phase 3)

```http
POST /api/v1/conversions
{"source_document_id": "<uuid>", "target_format": "html"}
```

Best-effort **flow layout** via PyMuPDF. Images land under `assets/` and are served at  
`GET /api/v1/documents/{id}/assets/{name}`. Limitations: [`docs/pdf-to-html-limitations.md`](docs/pdf-to-html-limitations.md).

## Security

Baseline checklist: [`../docs/SECURITY.md`](../docs/SECURITY.md).

## Layout

```text
backend/
  app/
    main.py          # FastAPI entry
    core/config.py   # settings
    api/             # routes (Phase 1+)
    converters/      # plugin converters (Phase 2+)
    storage/         # local file helpers
    database/        # Phase 5
    models/          # schemas / ORM
    workers/         # Celery (Phase 6)
  tests/
  requirements.txt
  requirements-dev.txt
  Dockerfile
```

## Next

[Phase 4 — Frontend](../plans/05-phase-4-frontend.md)
