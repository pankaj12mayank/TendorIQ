# Architecture Overview

> **Stack (current):** MySQL 8+, FastAPI, in-process asyncio job queue.  
> Optional: Clerk + JWT auth, Sentry. Redis/PostgreSQL are **not** required for local or default deployment.  
> See [AUDIT_STATUS.md](./AUDIT_STATUS.md) for remediation progress.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Client (React / Next.js 15)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │
│  │  Dashboard  │  │  Documents  │  │  Admin Panel            │   │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘   │
└─────────┼────────────────┼─────────────────────┼──────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              API (FastAPI) — prefix /api/v1                     │
│  Auth (JWT / Clerk) │ Rate limit │ Tenant context (JWT/header)  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Core APIs    │    │ In-process    │    │  AI providers │
│  tenders,     │    │ queue workers │    │  OpenAI, etc. │
│  documents,   │    │ OCR, parse,   │    │               │
│  analysis…    │    │ analysis jobs │    │               │
└───────┬───────┘    └───────┬───────┘    └───────────────┘
        │                    │
        ▼                    ▼
┌───────────────┐    ┌───────────────┐
│  MySQL 8+     │    │  Local / S3   │
│  (primary DB) │    │  file storage │
└───────────────┘    └───────────────┘
        │
        ▼
┌───────────────┐
│ Sentry (opt)  │
└───────────────┘
```

---

## Monorepo layout

| Path | Role |
|------|------|
| `apps/web` | Next.js frontend (`@tendoriq/web`) |
| `apps/api` | FastAPI backend |
| `packages/shared` | Shared TypeScript types and env helpers |
| `docs/` | Setup, API, audit status |

Orchestration: **pnpm workspaces** + **Turbo**. Root package name: `tenderiq`.

---

## Frontend (`apps/web`)

- App Router: `(auth)`, `(dashboard)`, `(onboarding)`, admin routes
- Data: TanStack Query, Zustand stores
- Auth: Clerk when configured; otherwise local JWT via `/api/v1/auth/login`
- API client: `NEXT_PUBLIC_API_URL` + `/api/v1/...` paths

**Libraries:** React 19, Next.js 15, Tailwind, Radix UI, Zod.

---

## Backend (`apps/api`)

```
api/src/
├── api/routers/       # tenders, documents, auth, files, ocr, …
├── api/router/        # analysis, billing, admin_platform, queue, …
├── api/dependencies/  # auth, tenant, permissions
├── core/              # models, rbac, database, queue, ai, middleware
└── main.py
```

**Libraries:** FastAPI, SQLAlchemy 2.x (async), Alembic, Pydantic, python-jose (JWT).

Database driver: **MySQL** via `DATABASE_URL` (see `docs/MYSQL_SETUP.md`).

---

## Background jobs

Jobs are processed **in-process** using asyncio (see `core/queue` and `QueueJob` model).  
`QUEUE_*` settings in `config.py` apply; **Redis is optional** and only used if configured for rate limiting.

Job types include OCR, parsing, and AI analysis. State is persisted in MySQL (`queue_jobs` table).

---

## Data flow

### Document upload

1. Client uploads via `/api/v1/files` or document init endpoints  
2. API stores metadata in MySQL and enqueues processing  
3. Worker runs OCR/parsing pipeline  
4. Status polled or surfaced in UI  

### Tenant isolation

1. JWT carries `tenant_id` (and ideally `membership_role`) after login/onboarding  
2. Optional header `X-Tenant-ID` for explicit tenant switch (validated against membership)  
3. Queries filter by `tenant_id` on tenant-scoped models (`TenantMixin`)

---

## Authentication

- **Local dev:** `SUPER_ADMIN_*` / `DEMO_USER_*` in `.env` → JWT from `/api/v1/auth/login`  
- **Production option:** Clerk → session; exchange or parallel JWT for API calls  
- **Platform admin:** `super_admin` role → `/api/v1/admin/platform/*` (requires `SuperAdmin` dependency)

RBAC matrix: `core/rbac.py` (`Permission` enum). Enforcement is being expanded per [AUDIT_REPORT.md](../AUDIT_REPORT.md).

---

## API surface

- Base path: **`/api/v1`** (not `/v1` alone)  
- Health: `/health`, `/health/ready` (outside version prefix in `api/base`)  
- OpenAPI: `/docs` in development  

---

## Monitoring

| Tool | Purpose |
|------|---------|
| Sentry | Error tracking (optional DSN) |
| `/api/v1/observability/*` | Metrics and health summaries |
| `audit_logs` table | Compliance / security trail |

---

## Deployment (typical)

- **Web:** Vercel or static host for Next.js  
- **API:** Railway, container, or VM running uvicorn  
- **DB:** Managed MySQL  
- **Files:** Local `./uploads` or object storage (configure in env)

Horizontal scaling of workers may later introduce Redis or a dedicated worker process; not required for the default monorepo setup.

---

## Technology decisions (current)

| Decision | Reason |
|----------|--------|
| FastAPI | Async API, OpenAPI, Pydantic v2 |
| MySQL | Primary store per project config and models |
| In-process queue | Simpler local/dev; jobs still persisted in DB |
| Clerk (optional) | Hosted auth; JWT fallback for API |
| pnpm + Turbo | Monorepo dev and build |
