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

- [ ] Phase 2 conversion API/service pattern exists
- [ ] Venv activated
- [ ] Add `pymupdf` to requirements and install into `.venv`

---

## Task checklist

### Task 3.1 — PDF text extraction

- [ ] Open PDF with PyMuPDF (`fitz`)
- [ ] Extract plain text per page
- [ ] Handle encrypted/unreadable PDFs with clear errors

### Task 3.2 — Position-aware extraction

- [ ] Use dict/rawdict or textpage APIs to get spans with bbox
- [ ] Group into lines/blocks heuristically (y-tolerance clustering)
- [ ] Preserve reading order approximately

### Task 3.3 — Images

- [ ] Extract embedded images where straightforward
- [ ] Save under `storage/outputs/{id}/assets/`
- [ ] Reference them from generated HTML with relative paths
- [ ] Skip or placeholder on extraction failure (warn, don’t crash entire job)

### Task 3.4 — Basic layout reconstruction

- [ ] Map blocks → `<p>`, headings heuristic (font size) → `<h1>`/`<h2>` optional
- [ ] Simple CSS for absolute or flow layout (choose one approach and document it)
  - **Flow layout (recommended v1):** stacked paragraphs, simpler, more robust
  - **Absolute layout:** closer to visual PDF, fragile for editing
- [ ] Multi-page: wrap pages in `<section data-page="n">`

### Task 3.5 — Implement `PDFToHTMLConverter`

- [ ] `app/converters/pdf_to_html.py` implementing `Converter`
- [ ] Register `pdf → html`
- [ ] Wire into existing `POST /api/v1/conversions` with `target_format="html"`

### Task 3.6 — Quality comparison harness

- [ ] Fixture PDFs: simple text, multi-page, image-containing
- [ ] Optional: convert HTML→PDF→HTML round-trip and note degradation (docs or test snapshots)
- [ ] Capture known limitations in `backend/docs/pdf-to-html-limitations.md`

### Task 3.7 — Preview integration

- [ ] Generated HTML previewable via Phase 1 preview endpoint
- [ ] Ensure asset URLs work when previewing (static mount under controlled path or API asset route)

### Task 3.8 — Tests

- [ ] Simple PDF produces HTML containing known strings
- [ ] Empty/corrupt PDF → 4xx/structured error
- [ ] Converter registry returns correct class for `(pdf, html)`

---

## Acceptance criteria

- [ ] Upload PDF → convert to HTML → download/preview works
- [ ] Limitations documented honestly
- [ ] Images extracted for at least one fixture (or explicitly deferred with ticket note)
- [ ] No conversion logic inside FastAPI route bodies

## Out of scope

- Perfect table reconstruction, OCR for scanned PDFs, DOCX, full visual parity
- Celery async (Phase 6) — keep sync via service layer

## Agent guidance

Prefer **flow layout HTML** for v1 so the React preview is readable. Absolute positioning can be a Phase 3.1 enhancement later without changing the converter interface.

---

**Previous:** [03-phase-2-html-to-pdf.md](03-phase-2-html-to-pdf.md)  
**Next:** [05-phase-4-frontend.md](05-phase-4-frontend.md)
