# Phase 3 — PDF → HTML (PyMuPDF, limited v1)

> **Parent index:** [00-INDEX.md](00-INDEX.md)  
> **Depends on:** [03-phase-2-html-to-pdf.md](03-phase-2-html-to-pdf.md)  
> **Next:** [05-phase-4-frontend.md](05-phase-4-frontend.md)  
> **Vision:** [`../Initial_idea.md`](../Initial_idea.md) — Phase 3 tasks 15–20

## Objective

Implement a **useful but limited** PDF → HTML converter using PyMuPDF: text extraction, basic positioning/blocks, optional images, and simple layout reconstruction. Set expectations: this will not perfectly recreate complex PDFs.

## Product expectation

```text
PDF → extract → blocks/images → reconstruct structure → HTML (v1 = best-effort)
```

Improve iteratively later; do not block the portfolio on perfect fidelity.

---

## Prerequisites

- [x] Phase 2 conversion API/service pattern exists
- [x] Venv activated
- [x] Add `pymupdf` to requirements and install into `.venv`

**TDD:** tests first. **Push:** `git push origin master` after acceptance criteria pass.

---

## Task checklist

### Task 3.1 — PDF text extraction

- [x] Open PDF with PyMuPDF (`fitz`)
- [x] Extract plain text per page
- [x] Handle encrypted/unreadable PDFs with clear errors

### Task 3.2 — Position-aware extraction

- [x] Use dict/rawdict or textpage APIs to get spans with bbox
- [x] Group into lines/blocks heuristically (y-tolerance clustering)
- [x] Preserve reading order approximately

### Task 3.3 — Images

- [x] Extract embedded images where straightforward
- [x] Save under `storage/outputs/{id}/assets/`
- [x] Reference them from generated HTML with relative paths
- [x] Skip or placeholder on extraction failure (warn, don’t crash entire job)

### Task 3.4 — Basic layout reconstruction

- [x] Map blocks → `<p>`, headings heuristic (font size) → `<h1>`/`<h2>` optional
- [x] Simple CSS for absolute or flow layout (choose one approach and document it)
  - **Flow layout (recommended v1):** stacked paragraphs, simpler, more robust
  - **Absolute layout:** closer to visual PDF, fragile for editing
- [x] Multi-page: wrap pages in `<section data-page="n">`

### Task 3.5 — Implement `PDFToHTMLConverter`

- [x] `app/converters/pdf_to_html.py` implementing `Converter`
- [x] Register `pdf → html`
- [x] Wire into existing `POST /api/v1/conversions` with `target_format="html"`

### Task 3.6 — Quality comparison harness

- [x] Fixture PDFs: simple text, multi-page, image-containing (generated in tests via PyMuPDF)
- [x] Optional: convert HTML→PDF→HTML round-trip and note degradation (docs or test snapshots)
- [x] Capture known limitations in `backend/docs/pdf-to-html-limitations.md`

### Task 3.7 — Preview integration

- [x] Generated HTML previewable via Phase 1 preview endpoint
- [x] Ensure asset URLs work when previewing (static mount under controlled path or API asset route)

### Task 3.8 — Tests

- [x] Simple PDF produces HTML containing known strings
- [x] Empty/corrupt PDF → 4xx/structured error
- [x] Converter registry returns correct class for `(pdf, html)`

---

## Acceptance criteria

- [x] Upload PDF → convert to HTML → download/preview works
- [x] Limitations documented honestly
- [x] Images extracted for at least one fixture (or explicitly deferred with ticket note)
- [x] No conversion logic inside FastAPI route bodies

## Out of scope

- Perfect table reconstruction, OCR for scanned PDFs, DOCX, full visual parity
- Celery async (Phase 6) — keep sync via service layer

## Agent guidance

Prefer **flow layout HTML** for v1 so the React preview is readable. Absolute positioning can be a Phase 3.1 enhancement later without changing the converter interface.

---

**Previous:** [03-phase-2-html-to-pdf.md](03-phase-2-html-to-pdf.md)  
**Next:** [05-phase-4-frontend.md](05-phase-4-frontend.md)
