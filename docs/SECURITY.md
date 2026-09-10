# Security baseline

Design notes for upload and conversion. Full enforcement lands in Phase 1+ and Phase 7; this document is the checklist so features do not ship without controls.

## Upload & storage

- **File size limits** — enforce `MAX_UPLOAD_BYTES` (default 10 MiB) before writing to disk.
- **MIME + extension validation** — allowlist by converter (e.g. `.html`/`.htm`, `.pdf`); reject mismatches.
- **Local storage only under project `storage/`** — uploads, outputs, and previews; never accept client-supplied absolute paths.
- **Secure serve** — resolve paths under storage roots; reject `..` / path traversal.

## Converters

- **No arbitrary filesystem reads** — converters receive only files already stored under `storage/`, or in-memory bytes from validated uploads.
- **HTML → PDF** — no SSRF: `LocalOnlyUrlFetcher` denies remote http(s)/ftp (placeholder image, no network). Only `file://` under the document asset root. No JS execution (WeasyPrint). Host allowlisting is a future opt-in.
- **No filesystem escape** — asset paths must stay under the uploaded document directory; paths outside raise `asset_path_denied`.
- **Sandboxed workers** — Phase 7: run conversion workers with least privilege / isolation.

## Deferred

- Full malware / AV scanning is **out of scope** for early phases.
- Auth, rate limits, and quotas: Phase 7.

## Related plans

- [Phase 0](../plans/01-phase-0-repo-and-dev-env.md) — this baseline
- [Phase 1](../plans/02-phase-1-backend-foundation.md) — validation & storage implementation
- [Phase 7](../plans/08-phase-7-public-service.md) — public hardening
