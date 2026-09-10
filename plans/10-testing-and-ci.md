# Testing & CI conventions

> Added after Phase 0. Applies to every later phase.  
> Parent index: [00-INDEX.md](00-INDEX.md)

## Branch & push

- Default branch: **`master`**
- Remote: `https://github.com/Muhammad-Akhtar/document-processing-service.git`
- After **each phase** is complete and acceptance criteria pass: commit, then **push to `master`**

## Test-driven development (required every phase)

Work **red → green → refactor**:

1. Write failing unit/API tests for the behavior in the current task.
2. Implement the minimum code to make those tests pass.
3. Refactor while keeping tests green.
4. Do **not** merge/push a phase with features that lack tests written first (or in the same commit cycle as the feature).

Cover happy paths **and** failure cases (validation errors, 404, oversized upload, path traversal, etc.).

Prefer fast unit tests for services/validators; use FastAPI `TestClient` / `httpx` for API routes.

Run locally before push:

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

- [ ] Features developed with **TDD** (tests first, then implementation)
- [ ] New behavior has tests (happy + failure paths)
- [ ] `pytest -q` passes in `backend/.venv`
- [ ] Plans / status tracker updated
- [ ] Commit message names the completed phase
- [ ] `git push origin master`
