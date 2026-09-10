# Phase 1 — Backend foundation (FastAPI)

> **Parent index:** [00-INDEX.md](00-INDEX.md)  
> **Depends on:** [01-phase-0-repo-and-dev-env.md](01-phase-0-repo-and-dev-env.md)  
> **Next:** [03-phase-2-html-to-pdf.md](03-phase-2-html-to-pdf.md)  
> **Vision:** [`../Initial_idea.md`](../Initial_idea.md) — Phase 1 tasks 1–8

## Objective

Ship a FastAPI backend that accepts uploads, validates files, stores them locally, exposes basic HTML/PDF viewing endpoints, and defines a **pluggable converter interface** — without putting conversion logic inside route handlers.

## Architecture rule (non-negotiable)

```text
Route → validate → storage service → (later) job → converter plugin
```

Routes must stay thin. Conversion lives under `app/converters/`.

---

## Prerequisites

- [x] Phase 0 complete (venv, skeleton, `/health`)
- [x] Testing & CI baseline: [10-testing-and-ci.md](10-testing-and-ci.md)
- [x] Venv activated: `backend\.venv\Scripts\Activate.ps1`

**Push rule:** when Phase 1 acceptance criteria pass, commit and `git push origin master` (CI must stay green).

**TDD:** write failing tests for each task before implementing. See [10-testing-and-ci.md](10-testing-and-ci.md).

---

## Task checklist

### Task 1.1 — Project architecture & app factory

- [x] Structure `app/main.py` (or `create_app()`) with CORS, exception handlers, router includes
- [x] Config via `pydantic-settings` (`STORAGE_ROOT`, max size, allowed MIME types)
- [x] Structured logging (stdlib or `structlog` — keep simple)

### Task 1.2 — Pydantic / domain models

Under `app/models/` (API schemas; DB models wait for Phase 5):

- [x] `DocumentMeta` — id, original_filename, content_type, size, stored_path, created_at
- [x] `UploadResponse` — document_id, filename, content_type, size
- [x] `ErrorResponse` — code, message, details
- [x] `ConversionRequest` stub — source_document_id, target_format (used Phase 2+)
- [x] `JobStatus` enum stub — `pending | processing | completed | failed` (used Phase 6)

### Task 1.3 — Converter base interface

`app/converters/base.py`:

```python
class Converter(Protocol):  # or ABC
    source_format: str
    target_format: str
    def convert(self, source_path: Path, destination_path: Path) -> ConversionResult:
        ...
```

- [x] `ConversionResult` with success, output_path, warnings, error
- [x] Registry map: `(source, target) → Converter` for later discovery
- [x] Placeholder modules: `html_to_pdf.py`, `pdf_to_html.py` (NotImplemented until Phase 2–3)

### Task 1.4 — File upload API

- [x] `POST /api/v1/documents` — multipart upload
- [x] Generate UUID document id
- [x] Save via storage service (not raw open() in the route)
- [x] Return `UploadResponse`
- [x] Tests with `httpx` + `TestClient` / `AsyncClient`

### Task 1.5 — File validation

Implement `app/core/validation.py` (or `storage/validation.py`):

- [x] Max file size (config-driven)
- [x] Allowed extensions whitelist (start: `.html`, `.htm`, `.pdf`, maybe `.css`/images later)
- [x] Content-type / magic-byte checks where practical
- [x] Reject path tricks in filenames (`../`, absolute paths)
- [x] Sanitize stored filenames

HTML-specific (early hooks for Phase 2 security):

- [x] Document that remote URL fetching in HTML must be disabled or allowlisted later
- [x] Reject empty files

### Task 1.6 — Local storage service

`app/storage/local.py`:

- [x] Paths under repo `storage/uploads/{document_id}/...`
- [x] `save_upload`, `get_path`, `delete`, `exists`
- [x] Ensure no path traversal outside `STORAGE_ROOT`
- [x] Optional metadata JSON sidecar next to file (until Postgres in Phase 5)

Secure serve:

- [x] `GET /api/v1/documents/{id}/download` streams file after id lookup (never take raw user path)
- [x] `DELETE /api/v1/documents/{id}`

### Task 1.7 — HTML viewer API

- [x] `GET /api/v1/documents/{id}/preview` for HTML: return sanitized/controlled HTML or a preview payload
- [x] Prefer serving through API with `Content-Security-Policy` suitable for preview (no arbitrary script if possible)
- [x] For v1, simple file return with correct media type is acceptable if CSP noted as follow-up

### Task 1.8 — PDF viewer API

- [x] Preview strategy A: return PDF bytes for browser built-in viewer
- [ ] Strategy B (optional): render first page to PNG via PyMuPDF (can wait until Phase 3 dependency install)
- [x] Document which strategy is default in OpenAPI description

### Task 1.9 — API versioning & OpenAPI polish

- [x] Prefix `/api/v1`
- [x] Tags: `health`, `documents`, `conversions` (empty router ok)
- [x] Meaningful response models and status codes (400 validation, 404 missing, 413 too large)

### Task 1.10 — Tests

- [x] Upload happy path
- [x] Reject oversized / bad extension
- [x] Download & delete
- [x] Path traversal attempts fail

---

## Suggested endpoints after Phase 1

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| POST | `/api/v1/documents` | Upload |
| GET | `/api/v1/documents/{id}` | Metadata |
| GET | `/api/v1/documents/{id}/download` | Download original |
| GET | `/api/v1/documents/{id}/preview` | Preview |
| DELETE | `/api/v1/documents/{id}` | Delete |

Conversion endpoints land in Phase 2–3 (sync) and Phase 6 (async jobs).

---

## Acceptance criteria

- [x] Thin routes; storage + validation in services
- [x] Converter ABC/Protocol + registry exist
- [x] Local storage under `storage/` with traversal protection
- [x] Upload/validate/download/delete/preview work via venv + uvicorn
- [x] pytest coverage for validation and upload flows
- [x] OpenAPI docs usable at `/docs`

## Out of scope

- WeasyPrint/PyMuPDF conversion (Phases 2–3)
- React UI, Postgres, Celery, S3

## Implementation tips for agents

1. Activate `backend/.venv` before running anything.
2. Keep all new deps in `requirements.txt` and install into venv.
3. Prefer absolute imports from `app.*`.
4. Do not call WeasyPrint from a route even in Phase 2 — call a converter class from a service.
5. **TDD:** tests first for each task; cover upload happy path, oversized/bad extension, download/delete, path traversal.

---

**Previous:** [01-phase-0-repo-and-dev-env.md](01-phase-0-repo-and-dev-env.md)  
**Next:** [03-phase-2-html-to-pdf.md](03-phase-2-html-to-pdf.md)
