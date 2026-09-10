# Phase 7 — Public service (auth, quotas, storage hardening)

> **Parent index:** [00-INDEX.md](00-INDEX.md)  
> **Depends on:** [07-phase-6-celery-redis.md](07-phase-6-celery-redis.md)  
> **Next:** [09-phase-8-scaling-observability.md](09-phase-8-scaling-observability.md)  
> **Vision:** [`../Initial_idea.md`](../Initial_idea.md) — Phase 7 tasks 40–47  
> **Note:** S3 is **deferred** until needed; keep local `storage/` until then (per `Initial_idea.md`).

## Objective

Make the service safe enough to expose beyond localhost: authentication, rate limiting, file quotas, stronger isolation, polished API docs. Add S3 + presigned URLs when leaving single-machine storage.

---

## Task checklist

### Task 7.1 — Authentication

- [ ] Choose approach: JWT (access/refresh) or session cookies — prefer JWT for API-first
- [ ] Register / login / me endpoints
- [ ] Bind documents & jobs to `owner_id`
- [ ] Frontend login/register screens
- [ ] Optional: anonymous limited tier for demo (strict quotas)

### Task 7.2 — Rate limiting

- [ ] Redis-based rate limits per IP and per user
- [ ] Separate limits for upload vs conversion
- [ ] Return `429` with clear headers/messages

### Task 7.3 — File quotas

- [ ] Per-user max storage bytes and max conversions/day
- [ ] Enforce on upload and enqueue
- [ ] Admin/config knobs in settings

### Task 7.4 — Local storage hardening (before S3)

- [ ] Confirm path traversal impossible
- [ ] Periodic cleanup job for expired anonymous files
- [ ] Secure content disposition; do not execute uploaded HTML on same origin as admin

### Task 7.5 — S3-compatible storage (when ready)

Only when local disk is insufficient:

- [ ] Storage interface already abstract? If not, introduce `StorageBackend` protocol (`local` | `s3`)
- [ ] Upload to bucket; DB stores keys
- [ ] Presigned download URLs
- [ ] Migrate script optional
- [ ] Keep local backend for dev/venv debugging

### Task 7.6 — Virus / malware scanning (progressive)

- [ ] Start with extension/MIME/size (already done)
- [ ] Optional ClamAV in compose for uploads
- [ ] Fail closed on positive detection

### Task 7.7 — Security isolation

- [ ] Workers run with least privilege
- [ ] HTML converter network disabled
- [ ] Resource limits (CPU/memory) on worker containers
- [ ] Consider separate worker queues for untrusted HTML

### Task 7.8 — API documentation

- [ ] OpenAPI complete with auth schemes
- [ ] Examples for upload + async convert + poll
- [ ] Public `README` quickstart for demo users

### Task 7.9 — Nginx (optional for deploy)

- [ ] Reverse proxy config for API + frontend static
- [ ] Upload size limits at proxy layer too

---

## Acceptance criteria

- [ ] Unauthenticated users cannot access another user’s documents
- [ ] Rate limits and quotas enforced
- [ ] Storage backend abstraction allows local (venv debug) and S3 (prod)
- [ ] Security notes from Phase 0 verified against running system

## Out of scope

- Full Kubernetes HPA / multi-region
- Perfect PDF→HTML quality work (iterate separately)

---

**Previous:** [07-phase-6-celery-redis.md](07-phase-6-celery-redis.md)  
**Next:** [09-phase-8-scaling-observability.md](09-phase-8-scaling-observability.md)
