# Phase 4 — Frontend (React + TypeScript)

> **Parent index:** [00-INDEX.md](00-INDEX.md)  
> **Depends on:** [04-phase-3-pdf-to-html.md](04-phase-3-pdf-to-html.md) (backend converters working)  
> **Next:** [06-phase-5-database.md](06-phase-5-database.md)  
> **Vision:** [`../Initial_idea.md`](../Initial_idea.md) — Phase 4 tasks 21–26

## Objective

Build a React + TypeScript UI for upload, conversion, preview, download/delete, and a simple in-browser history. Match the wireframe spirit in `Initial_idea.md` without overbuilding.

## Prerequisites

- [ ] Backend convertible via `/api/v1` (Phases 1–3)
- [ ] CORS configured for Vite/dev origin in backend settings
- [ ] Node.js 20+ installed

---

## Task checklist

### Task 4.1 — Scaffold frontend

- [ ] Create Vite + React + TypeScript app in `frontend/`
- [ ] ESLint + basic folder structure: `src/api`, `src/components`, `src/pages`, `src/types`
- [ ] Env: `VITE_API_BASE_URL=http://localhost:8000`
- [ ] `frontend/README.md` with `npm install` / `npm run dev`

### Task 4.2 — API client

- [ ] Typed fetch/axios wrapper for documents & conversions
- [ ] Shared TypeScript types mirroring Pydantic schemas
- [ ] Error toast/banner for API failures

### Task 4.3 — Drag & drop uploads

- [ ] Drop zone + file picker
- [ ] Accept HTML/PDF (extend later)
- [ ] Client-side size check mirroring backend max
- [ ] Upload progress (XHR/fetch progress if available)

### Task 4.4 — Progress indicator

- [ ] Upload progress bar
- [ ] Conversion in-progress state (sync API: spinner until response; later swap to job polling in Phase 6)

### Task 4.5 — Document preview

- [ ] PDF: `<iframe>` / `<object>` / pdf.js — pick one simple approach
- [ ] HTML: sandboxed iframe (`sandbox` attributes) loading preview URL
- [ ] Empty state when nothing selected

### Task 4.6 — Convert / download / delete actions

- [ ] Convert button: choose target format based on source (HTML→PDF, PDF→HTML)
- [ ] Download original and converted outputs
- [ ] Delete with confirm dialog

### Task 4.7 — Conversion history (client-side first)

- [ ] Until Postgres (Phase 5), keep history in `localStorage` or session list from current uploads
- [ ] Show filename, type, status, timestamps
- [ ] Clicking a row loads preview

### Task 4.8 — App shell

Wireframe targets from vision:

```text
DocConvert | Upload | Preview | Convert | Download | Delete
```

- [ ] Simple top bar with product name
- [ ] Single main workspace (avoid dashboard clutter)
- [ ] Responsive enough for desktop-first; usable on tablet

### Task 4.9 — Dev ergonomics

- [ ] Proxy or CORS so local Vite ↔ uvicorn works
- [ ] Document dual-run: terminal 1 backend venv, terminal 2 `npm run dev`

---

## Acceptance criteria

- [ ] User can upload HTML, convert to PDF, preview/download without using Swagger
- [ ] User can upload PDF, convert to HTML, preview
- [ ] Delete works; history lists recent items
- [ ] Frontend README is enough for an agent to run the UI

## Out of scope

- Auth UI (Phase 7)
- Perfect design system; keep clean and functional
- Server-side history (Phase 5)

## Agent notes

Backend remains source of truth for validation. Frontend checks are UX only. When Phase 6 lands, replace blocking convert calls with `job_id` polling — design the convert button handler behind a small API module so that swap is localized.

---

**Previous:** [04-phase-3-pdf-to-html.md](04-phase-3-pdf-to-html.md)  
**Next:** [06-phase-5-database.md](06-phase-5-database.md)
