# Frontend (DocConvert)

React + TypeScript UI for upload, preview, convert, download/delete, and local history.

## Prerequisites

- Node.js **22+** (Vitest 5 / Vite 8 require modern Node; CI uses Node 22)
- Backend running (venv uvicorn on `:8000` or Docker API on `:8008`)

## Setup

```powershell
cd frontend
npm install
```

Copy env example if you need overrides:

```powershell
Copy-Item .env.example .env
```

## Run

### Docker (full stack — recommended on Windows)

From the **repo root** (WeasyPrint works inside the Linux API image):

```powershell
docker compose up --build
```

UI: http://127.0.0.1:5173 — nginx serves the built app and proxies `/api` to the `api` service.

### Local Vite (dual terminals)

```powershell
# terminal 1 — backend (venv)
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# terminal 2 — frontend
cd frontend
npm run dev
```

Open http://127.0.0.1:5173

Vite proxies `/api` and `/health` to `VITE_PROXY_TARGET` (default `http://127.0.0.1:8000`).

### Hybrid (Docker API + local Vite)

```powershell
# terminal 1 — from repo root
docker compose up --build api

# terminal 2
cd frontend
$env:VITE_PROXY_TARGET="http://127.0.0.1:8008"
npm run dev
```
## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Vite dev server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm test` | Vitest unit + integration tests |
| `npm run lint` | Oxlint |

## Notes

- History is stored in `localStorage` until Phase 5 (Postgres).
- Convert is sync today; Phase 6 can swap to job polling behind `src/api/documents.ts`.
