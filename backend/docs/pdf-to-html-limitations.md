# PDF → HTML limitations (v1)

This converter is **best-effort**, not a perfect visual replica of the PDF.

## What v1 does

- Extracts text via PyMuPDF (`page.get_text("dict")`) in approximate reading order
- Builds **flow layout** HTML (`<section data-page>`, `<p>`, optional `<h2>` by font size)
- Extracts embedded images into `assets/` next to the HTML when possible
- Surfaces encrypted / unreadable PDFs as structured errors

## What v1 does not do

- Perfect table reconstruction
- Absolute/visual positioning matching the PDF canvas
- OCR for scanned (image-only) pages
- Form fields, annotations, or JavaScript
- Exact fonts / kerning / multi-column layouts
- Password-protected PDFs (no password API yet)

## Round-trip note

`HTML → PDF → HTML` will lose styling and structure. Prefer HTML→PDF as the polished path; treat PDF→HTML as extraction/preview aid.

## Preview & assets

Generated HTML uses relative `assets/...` URLs. When previewing at  
`GET /api/v1/documents/{id}/preview`, the browser resolves those to  
`GET /api/v1/documents/{id}/assets/{name}` (path traversal blocked).
