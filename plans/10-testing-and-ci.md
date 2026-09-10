# Testing & CI conventions

> Added after Phase 0. Applies to every later phase.  
> Parent index: [00-INDEX.md](00-INDEX.md)

## Branch & push

- Default branch: **`master`**
- Remote: `https://github.com/Muhammad-Akhtar/document-processing-service.git`
- After **each phase** is complete and acceptance criteria pass: commit, then **push to `master`**

## Unit / API tests (required every phase)

For each feature or endpoint added in a phase:

1. Add tests under `backend/tests/` (and later `frontend/` test dirs).
2. Cover happy path **and** failure cases called out in that phase (validation errors, 404, oversized upload, etc.).
3. Prefer fast unit tests for services/validators; use FastAPI `TestClient` / `httpx` for API routes.
4. Run locally before push:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
ruff check app tests
```

## CI (GitHub Actions)

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

- Triggers on **push** and **pull_request** to `master`
- Installs backend deps, runs **ruff**, then **pytest**

Phase 8 may extend CI (frontend build, Docker image, deploy). Do **not** wait until Phase 8 to keep the backend green — every phase push must pass this workflow.

## Agent checklist before phase push

- [ ] New behavior has tests
- [ ] `pytest -q` passes in `backend/.venv`
- [ ] Plans / status tracker updated
- [ ] Commit message names the completed phase
- [ ] `git push origin master`
