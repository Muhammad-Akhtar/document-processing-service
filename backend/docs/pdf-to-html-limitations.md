# PDF → HTML limitations (v2)

This converter is **layout-aware and best-effort**, not a perfect semantic reconstruction of the original document.

## What v2 does

- Extracts structured text via PyMuPDF (`page.get_text("dict")`) — blocks → lines → **spans**
- Builds **absolute visual layout** HTML:
  - Page containers sized from `page.rect` (`width`/`height` in pt)
  - Each span positioned with `left`/`top` from its bounding box
  - Font size, approximate font family, and text color preserved in CSS
  - Bold / italic inferred from font name and span flags (`<strong>` / `<em>`)
- Maps URI annotations via `page.get_links()` onto overlapping spans as `<a href="...">` (`http` / `https` / `mailto`)
- Renders vector drawings from `page.get_drawings()`:
  - Filled rectangles (including WeasyPrint **even-odd** double-rect section underlines)
  - Axis-aligned stroked line segments
  - Skips full-page white background washes
- Extracts embedded images into `assets/` and positions them when bbox data is available
- Surfaces encrypted / unreadable PDFs as structured errors

## What v2 does not do

- Perfect **semantic** table / list reconstruction (two-column text may *look* aligned but is not a `<table>`)
- OCR for scanned (image-only) pages
- Form fields, non-URI annotations, or JavaScript
- Exact embedded font files / perfect kerning
- Complex curves, diagonal strokes, or full SVG path fidelity
- Password-protected PDFs (no password API yet)

## Round-trip note

`HTML → PDF → HTML` will still lose original semantic structure. Prefer HTML→PDF as the polished authoring path; treat PDF→HTML as visual extraction / preview aid.

## Preview & assets

Generated HTML uses relative `assets/...` URLs. When previewing at  
`GET /api/v1/documents/{id}/preview`, the browser resolves those to  
`GET /api/v1/documents/{id}/assets/{name}` (path traversal blocked).
