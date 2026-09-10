# Phase 2 — First converter: HTML → PDF (WeasyPrint)

> **Parent index:** [00-INDEX.md](00-INDEX.md)  
> **Depends on:** [02-phase-1-backend-foundation.md](02-phase-1-backend-foundation.md)  
> **Next:** [04-phase-3-pdf-to-html.md](04-phase-3-pdf-to-html.md)  
> **Vision:** [`../Initial_idea.md`](../Initial_idea.md) — Phase 2 tasks 9–14

## Objective

Deliver a high-quality **HTML → PDF** path using WeasyPrint, as a pluggable converter, with CSS/images/fonts support, clear errors, and download of generated PDFs. This is the first “real product” conversion.

## Expectation

HTML → PDF is the **primary polished converter**. PDF → HTML (Phase 3) will be intentionally limited at first.

---

## Prerequisites

- [ ] Phase 1 upload/storage/converter interface done
- [ ] Venv activated
- [ ] WeasyPrint system dependencies available on the machine **or** use Docker for conversion tests (see Phase 0 Windows note)

---

## Task checklist

### Task 2.1 — Install WeasyPrint (+ HTML helpers)

- [ ] Add to requirements: `weasyprint`, `beautifulsoup4`, `lxml`
- [ ] `pip install` into `.venv`
- [ ] Document Windows native lib setup in `backend/README.md`
- [ ] Optional: extend Docker image with WeasyPrint OS packages for reliable CI

### Task 2.2 — Implement `HTMLToPDFConverter`

`app/converters/html_to_pdf.py`:

- [ ] Implements `Converter` from Phase 1
- [ ] `source_format="html"`, `target_format="pdf"`
- [ ] Reads HTML file (and optional sibling assets directory)
- [ ] Writes PDF under `storage/outputs/{job_or_doc_id}/...`
- [ ] Register in converter registry

### Task 2.3 — Inline CSS support

- [ ] Ensure `<style>` blocks in HTML are honored (WeasyPrint default strength)
- [ ] Support linked local CSS files that were uploaded/bundled with the document
- [ ] Tests with fixture HTML containing inline CSS (colors, fonts, margins)

### Task 2.4 — Images and fonts

- [ ] Relative image paths resolve against document base URL/path (local only)
- [ ] **Disable** fetching arbitrary remote URLs by default (SSRF / untrusted HTML — see security)
- [ ] Document how to allowlist specific hosts later if needed
- [ ] Basic `@font-face` / local font file support if feasible; otherwise document limitation

### Task 2.5 — PDF metadata

- [ ] Set title/author/creator where WeasyPrint API allows (from HTML `<title>` or request fields)
- [ ] Store output metadata alongside file (size, page count if cheap to obtain)

### Task 2.6 — Conversion service + API (sync for now)

Until Celery (Phase 6), sync conversion is OK **behind a service**:

- [ ] `POST /api/v1/conversions` body: `{ "document_id": "...", "target_format": "pdf" }`
- [ ] Service loads document, picks converter, runs `convert()`, stores output
- [ ] Response includes `output_document_id` / download URL
- [ ] Do **not** bury WeasyPrint calls inside the route function body

### Task 2.7 — Conversion errors

- [ ] Map WeasyPrint failures to structured `ErrorResponse`
- [ ] Distinguish validation errors (unsupported source) vs conversion engine errors
- [ ] Log stack traces server-side; return safe messages to clients

### Task 2.8 — Download generated PDF

- [ ] `GET /api/v1/documents/{output_id}/download` already from Phase 1 should cover outputs if stored as documents
- [ ] Or dedicated `GET /api/v1/conversions/{id}/download`
- [ ] Correct `Content-Type: application/pdf` and filename disposition

### Task 2.9 — Tests & fixtures

- [ ] `tests/fixtures/sample.html` with inline CSS + local image
- [ ] Test successful conversion produces non-empty PDF
- [ ] Test reject PDF→PDF via this converter
- [ ] Test remote `http://` image URL blocked or ignored per policy

---

## Security checklist (HTML)

From [`../Initial_idea.md`](../Initial_idea.md):

- [ ] No arbitrary external network fetches during render (default deny)
- [ ] No access to server filesystem outside document asset root
- [ ] No JavaScript execution during conversion
- [ ] Size limits on HTML and embedded assets

---

## Acceptance criteria

- [ ] `HTMLToPDFConverter` registered and unit-tested
- [ ] End-to-end: upload HTML → convert → download PDF works in venv
- [ ] Inline CSS visible in output PDF (spot-check)
- [ ] Errors are structured; routes remain thin
- [ ] Security defaults for untrusted HTML documented and enforced where possible

## Out of scope

- Async jobs (Phase 6)
- High-fidelity PDF → HTML (Phase 3)
- Frontend polish (Phase 4)

---

**Previous:** [02-phase-1-backend-foundation.md](02-phase-1-backend-foundation.md)  
**Next:** [04-phase-3-pdf-to-html.md](04-phase-3-pdf-to-html.md)
