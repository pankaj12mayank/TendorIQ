# TenderIQ — System Audit Report

**Generated:** 2026-05-22
**Scope:** Full monorepo (frontend, backend, shared, configs, CI/CD, deployment)
**Auditor:** opencode AI

---

## 1. Executive Summary

**System Health Score: 48/100**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Frontend | 55 | Well-structured but heavy mock data, dual API clients, no server-side auth |
| Backend | 45 | Solid model layer, but duplicate routers, sync boto3, missing migrations |
| Database | 40 | MySQL vs PostgreSQL conflict, missing indexes, no migration history |
| CI/CD | 30 | npm in pnpm project, mock tests, no Dockerfile, disabled backend deploy |
| Deployment | 35 | No Docker, env contradictions, API excluded from pnpm workspace |
| Security | 50 | Tenant ID nullable in 54 queries, no webhook signature, Clerk keys as placeholders |

**Production Readiness: NOT READY**

The project is mid-migration from PostgreSQL+Redis+ARQ to MySQL+inline-tasks but the migration is incomplete. Configs, shared package, CI/CD, and documentation exist in a contradictory state. Multiple critical features (billing, analysis, review, notifications) return mock data only.

---

## 2. Critical Issues (Must Fix First)

- **apps/api excluded from pnpm workspaces** — `pnpm-workspace.yaml` only includes `apps/web` and `packages/*`; `apps/api` is absent. `pnpm --filter @tendoriq/api` will fail. (`pnpm-workspace.yaml:1`)
- **MySQL vs PostgreSQL architectural conflict** — `.env` uses `mysql+aiomysql://`, shared `env.ts` builds `postgresql+asyncpg://` URLs, `alembic.ini` hardcodes PostgreSQL, CI/CD spins up PostgreSQL:15. (`./.env`, `packages/shared/src/env.ts:85`, `apps/api/alembic.ini:1`)
- **CI uses `npm install` in pnpm monorepo** — All CI workflows use `npm install` and `npm run` which cannot resolve `workspace:*` dependencies. (`./.github/workflows/ci.yml:15`)
- **Two frontend API clients with inconsistent auth** — `lib/api.ts` sends no auth headers (used by `use-documents.ts`, `use-ocr.ts`, `use-onboarding.ts`), `lib/api-client.ts` sends Bearer token (used by `use-api.ts`, `use-admin.ts`, `use-analytics.ts`). Hooks using `api.ts` will get 401 errors on authenticated endpoints. (`apps/web/src/lib/api.ts:1`, `apps/web/src/lib/api-client.ts:1`)
- **Three incompatible role/permission systems** — `lib/permissions.ts` defines roles `super_admin | admin | manager | analyst | viewer | user | owner`; `components/auth/rbac.tsx` uses `super_admin | tenant_admin | user`; backend `core/rbac.py` uses `super_admin | owner | admin | member | viewer`. Role checks produce inconsistent results. (`apps/web/src/lib/permissions.ts:5`, `apps/web/src/components/auth/rbac.tsx:15`, `apps/api/src/core/rbac.py:14`)
- **Storage client uses synchronous boto3** — `StorageService.client` performs all S3 operations (upload, delete, list) synchronously via `boto3.client`, blocking the async event loop in every FastAPI endpoint. (`apps/api/src/core/storage/client.py:38`)
- **Next.js ignores build errors in production** — `next.config.ts` sets `eslint.ignoreDuringBuilds: true` and `typescript.ignoreBuildErrors: true` in production, hiding real errors at deploy time. (`apps/web/next.config.ts:12`)
- **No Dockerfile** — `deploy.yml` references `apps/api/Dockerfile` but no Dockerfile exists anywhere in the repo. (`./.github/workflows/deploy.yml:33`)
- **Duplicate auth route registration** — `super_admin.py` and `auth.py` both register under `/auth` prefix with overlapping routes (`POST /auth/login` vs `POST /auth/token`, both have `GET /auth/me`). (`apps/api/src/api/router/super_admin.py:18`, `apps/api/src/api/routers/auth.py:15`)
- **Mock data in 4 critical features** — `use-billing.ts`, `use-analysis.ts`, `use-review.ts`, `use-notifications.ts` all return hardcoded mock data with artificial `setTimeout` delays. No API calls are made. (`apps/web/src/hooks/use-billing.ts:1`, `apps/web/src/hooks/use-analysis.ts:1`, `apps/web/src/hooks/use-review.ts:1`, `apps/web/src/hooks/use-notifications.ts:1`)

---

## 3. High Priority Issues

### Performance
- **Synchronous boto3 blocks async loop** — All S3 operations (upload, delete, list, copy) run synchronously via `boto3.client`. Use `aioboto3` or run in thread pool. (`apps/api/src/core/storage/client.py:151`)
- **Recursive polling without cleanup** — `pollDocumentStatus()` and `pollStatus()` in OCR use recursive `setTimeout` but never clean up on component unmount, causing potential memory leaks. (`apps/web/src/hooks/use-documents.ts:210`, `apps/web/src/hooks/use-ocr.ts:130`)
- **Two frontend API clients** — `api.ts` (51 lines, no auth) and `api-client.ts` (126 lines, with auth) are both exported as `api`. Importing from the wrong one silently breaks auth. (`apps/web/src/lib/api.ts`, `apps/web/src/lib/api-client.ts`)

### Architecture
- **Version drift between requirements.txt and package.json** — FastAPI `==0.115.0` vs `^0.115.6`, uvicorn `==0.30.6` vs `^0.34.0`, pydantic `==2.9.2` vs `^2.10.5`, sentry `==2.14.0` vs `^2.22.0`. 8 packages have mismatched versions. (`apps/api/requirements.txt`, `apps/api/package.json`)
- **Root tsconfig.js has conflicting settings** — `noEmit: true` and `declaration: true` are both set; declarations will never be emitted. (`tsconfig.json:5`)
- **`clean` script uses `rm -rf`** — Fails on Windows without Git Bash. (`package.json:30`)
- **Alembic versions directory is empty** — Only a `.gitkeep` file exists. No migration history means production DB cannot be migrated. (`apps/api/alembic/versions/.gitkeep`)
- **`admin_store.py` uses JSON file persistence** — AI providers and platform users are stored in `.tenderiq/*.json` files alongside the DB, creating a fragile dual-persistence pattern. (`apps/api/src/core/admin_store.py`)

### Data Integrity
- **Tenant ID can be None in 54+ query locations** — Routes check `if not current_user.tenant_id` but service layer and queries can receive `None` as tenant_id, potentially exposing cross-tenant data. (Throughout `documents.py`, `tenders.py`, `billing.py`, etc.)
- **Email system seed failure is silently swallowed** — `main.py` lifespan wraps email seeding in try/except and only logs warning on failure. DB may be missing required email tables. (`apps/api/src/main.py:66`)
- **No file virus scanning on upload** — Documents are accepted and stored without any antivirus/clamav check. (`apps/api/src/api/routers/documents.py`)

---

## 4. Medium Issues

### UI / UX
- **No `loading.tsx` files** — Each page implements inline loading states; no route-level Suspense boundaries exist. (Missing throughout `apps/web/src/app/`)
- **No `not-found.tsx`** — Missing custom 404 page; users see default Next.js 404. (Missing in `apps/web/src/app/`)
- **No favicon, robots.txt, or sitemap.xml** — `public/` only contains `manifest.json`. SEO and branding assets missing. (`apps/web/public/`)
- **Two toast systems in use** — `sonner` (used in app-providers, admin, forgot-password) and custom `toast-store.ts` (used in upload, use-api mutations) create inconsistent notifications. (`apps/web/src/components/ui/sonner.tsx`, `apps/web/src/stores/toast-store.ts`)
- **`ProtectedRoute` uses `window.location.href`** — `GuestRoute` component does hard navigation instead of `router.push()`, causing full page reloads. (`apps/web/src/components/auth/protected-route.tsx:45`)
- **`sign-in-clerk.tsx` forces `/onboarding` redirect** — `forceRedirectUrl="/onboarding"` will trap users who already completed onboarding. (`apps/web/src/app/(auth)/sign-in/sign-in-clerk.tsx:5`)
- **Analytics route is a client-side redirect** — `/dashboard/analytics` redirects to `/dashboard/admin?module=analytics` via `router.push()`, no server-side redirect. (`apps/web/src/app/(dashboard)/dashboard/analytics/page.tsx`)
- **Settings route is a redirect-only page** — `/dashboard/settings` only redirects based on role with no content of its own. (`apps/web/src/app/(dashboard)/dashboard/settings/page.tsx`)

### Cleanup
- **Duplicate `admin-auth.py` and `admin_auth.py`** — Two nearly identical files exist due to what appears to be a merge conflict. (`apps/api/src/api/router/admin-auth.py`, `apps/api/src/api/router/admin_auth.py`)
- **Duplicate health endpoints** — Both `base.py` (production) and a separate `health.py` (orphaned) define `/health` routes. (`apps/api/src/api/base.py:12`, `apps/api/src/health.py`)
- **Two `TenantMiddleware` classes** — `core/middleware.py` has a simple version (no DB), `core/tenant_middleware.py` has an enhanced version (with DB). Only the enhanced one is registered in `main.py`. (`apps/api/src/core/middleware.py:20`, `apps/api/src/core/tenant_middleware.py`)
- **Vestigial TypeScript files** — `plan-middleware.ts`, `usage-middleware.ts`, `billing-routes.ts` exist but are not imported anywhere. (In `apps/api/src/middleware/` and `apps/api/src/routes/`)
- **`admin-content-editor.tsx` in landing components** — Admin content editor lives inside the landing page components directory; violates separation of concerns.

### Error Handling
- **`use-analytics.ts` `fetchMetrics()` has no try/catch** — Promise rejection is silently swallowed. No error state, no user feedback. (`apps/web/src/hooks/use-analytics.ts:29`)
- **`use-auth.tsx` `fetchMe()` returns null on any error** — Auth initialization silently fails; no retry, no error state exposed. (`apps/web/src/hooks/use-auth.tsx:120`)
- **`use-admin.ts` `cancelJob()`, `pauseJob()`, `resumeJob()` are client-side only** — These functions update local state but make no API calls. No backend endpoints exist for these operations. (`apps/web/src/hooks/use-admin.ts:425`)
- **`use-admin.ts` PDF export returns JSON** — Line 542 has `format === 'pdf' ? 'json' : format`, meaning PDF exports always get JSON. (`apps/web/src/hooks/use-admin.ts:542`)

---

## 5. Low Issues

### Cosmetic / Minor
- **`use-admin.ts` prompts endpoint uses trailing slash** — `/api/v1/prompts/` while the rest of API uses no trailing slash (`/api/v1/tenders`). (`apps/web/src/hooks/use-admin.ts:350`)
- **Hardcoded `?limit=100` in audit URL** — Concatenated directly into URL string instead of using `params` option. (`apps/web/src/hooks/use-admin.ts:528`)
- **`onboarding-store.ts` exports unrelated types** — `Plan` and `ExpertiseCategory` types are exported from a Zustand store file. (`apps/web/src/stores/onboarding-store.ts:145`)
- **`rbac.tsx` `rolePermissions` duplicates `permissions.ts`** — Same permission mappings defined in two places; maintenance burden. (`apps/web/src/components/auth/rbac.tsx:40`)
- **`use-admin.ts` creates prompts with `isActive` → `is_active` mapping** — Manual snake_case/camelCase conversion instead of using a centralized serializer. (`apps/web/src/hooks/use-admin.ts:380`)
- **`app-sidebar.tsx` maps `manager`, `analyst`, `viewer` all to `user`** — These roles get identical sidebar navigation as regular users; no differentiated nav. (`apps/web/src/components/design-system/app-sidebar.tsx:50`)
- **`_tender_to_dict` uses `getattr` for every field** — Service layer serialization uses defensive `getattr()` instead of proper SQLAlchemy attribute access. (`apps/api/src/api/services/tender_service.py:63`)
- **`MOCK_QUEUE_METRICS` and `MOCK_FAILURES` used in production admin endpoints** — Admin platform routes mix real DB queries with hardcoded mock metrics. (`apps/api/src/api/router/admin_platform.py:306`)
- **`sign-out-dialog.tsx` uses `console.log` for auth state** — Development leftover. (`apps/web/src/components/auth/sign-out-dialog.tsx:50`)

---

## 6. Broken Flows Map

### Auth Flow
```
Frontend                              Backend
────────                              ───────
Sign-in page
├─ Clerk SSO → POST /auth/clerk/webhook → Logs webhook only, no user creation
│   └─ use-auth.tsx raw fetch → GET /auth/me → OK, but no tenant context
│
└─ Local JWT → POST /auth/login (super_admin.py) → JWT returned
    └─ use-auth.tsx fetchMe() → GET /auth/me → Works for super_admin/demo
    └─ BUT: POST /auth/token (auth.py) → Also handles login with Depends(get_current_user) — circular!
    └─ Token stored in localStorage + cookie (double exposure)

❌ Clerk webhook only logs events — no user/tenant DB creation
❌ /auth/login and /auth/token both handle auth — duplicate routes
❌ routes/auth.py uses Depends(get_current_user) for login — requires token to get token
❌ Email triggers are console.log stubs (useEmailTriggers)
```

### Tender Flow
```
Frontend                               Backend
────────                               ───────
dashboard/tenders → useTenders() → GET /api/v1/tenders → TenderService → DB
dashboard/tenders (mock data!) ← mockTenders hardcoded, no API call

dashboard/tenders/analysis → useAnalysis() → NO API CALL (100% mocked)
dashboard/tenders/review → useReview() → NO API CALL (100% mocked)

❌ Tenders list page uses mock data, not API
❌ Analysis page never connects to backend
❌ Review page never connects to backend
❌ Backend has NO analysis endpoints
```

### CRM / Billing Flow
```
Frontend                               Backend
────────                               ───────
dashboard/billing → useBilling() → NO API CALL (100% mocked)
dashboard/usage → useBilling() → NO API CALL (100% mocked)
dashboard/bids → mockBids hardcoded → NO API CALL

Backend:
GET /api/v1/billing/subscription → BillingService (exists but frontend never calls)
GET /api/v1/billing/usage → BillingService (exists but frontend never calls)
GET /api/v1/billing/plans → Hardcoded plans (exists but frontend never calls)

❌ Entire billing frontend is mocked — never connects to backend
❌ Bids page uses mock data
❌ Backend billing endpoints exist but frontend doesn't use them
❌ Billing limits are not enforced anywhere (PlanLimits exists but unused)
```

### Notification Flow
```
Frontend                               Backend
────────                               ───────
NotificationBell → useNotifications() → NO API CALL (100% mocked)
Email triggers → useEmailTriggers() → console.log() only

Backend:
EmailSystem router exists but frontend never calls it
EmailQueueItem DB model exists but has no sender implementation

❌ Entire notification system is client-side only
❌ Email triggers are console.log stubs
❌ No WebSocket/SSE for real-time notifications
```

---

## 7. API Mismatch Table

| Frontend Call | Method | Path | Backend Expects | Mismatch |
|---|---|---|---|---|
| `useTenders()` | GET | `/api/v1/tenders` | Returns `PaginatedResponse` | **OK** — but frontend Tender type has `organization_id` while backend model has `organization_id` as nullable UUID — mismatch if organization not provided |
| `useDocumentsApi.fetchDocuments()` | GET | `/api/v1/documents/list` | Returns `DocumentListResponse` | **Uses `api.ts` (no auth)** — will fail with 401 |
| `useDocumentsApi.deleteDocument()` | DELETE | `/api/v1/documents/{id}` | Backend sets `permanently` via Query param | **Frontend sends `permanently` as body param** — mismatch in how permanent flag is sent |
| `useDocumentsApi.retryDocuments()` | POST | `/api/v1/documents/retry` | Expects `RetryRequest` with `document_ids` | Frontend sends `{ document_ids: string[] }` — **OK** |
| `useDocumentsApi.handleRetryFailed()` | fetch() | Raw fetch, no path | N/A | **Bypasses API client entirely** — uses raw fetch on line 25-26 |
| `useAuth.loginWithCredentials()` | POST | `/api/v1/auth/login` | Expects `LoginRequest` | **Two routes handle this**: `super_admin.py` (email/password) and `auth.py` (`/token` via `Depends(get_current_user)`) — ambiguous |
| `useAuth.fetchMe()` | GET | `/api/v1/auth/me` | Returns `UserResponse` | `super_admin.py` ALSO has `GET /auth/me` with different response shape — **two different `/me` responses** |
| `useAdminApi.fetchUsers()` | GET | `/api/v1/admin/platform/users` | Returns `{ users: User[], total: number }` | Frontend expects `{ users: User[] }` — total is extra, **no pagination info returned** despite `limit: 500` |
| `useAdminApi.fetchBilling()` | GET | `/api/v1/admin/platform/billing` | Returns `{ plans, subscriptions, invoices, stats }` | **Frontend only uses `{ plans }`** — subscriptions and invoices are ignored |
| `useAdminApi.fetchPrompts()` | GET | `/api/v1/prompts/` (trailing slash) | No backend endpoint matches `GET /prompts/` | **404 — no prompt listing endpoint exists** on backend |
| `useAnalytics.fetchMetrics()` | GET | `/api/v1/admin/platform/analytics/summary` | Returns `{ totalUsers, apiCallsToday, activeJobs, errorRate, monthlyCost, usage }` | Frontend hardcodes `activeDocuments: 0` and `setMetrics()` entirely — **response shape disconnect** |
| `useOcr.processDocument()` | POST | `/api/v1/ocr/process/{documentId}` | Returns `{ success, job_id, document_id, status }` | **Uses `api.ts` (no auth)** — will fail with 401 |
| `useOnboarding.submitStep()` | POST | `/api/v1/onboarding/step` | Backend onboarding router exists | **Uses `api.ts` (no auth)** — will fail with 401 |
| Admin `useAdminStore.fetchUsers()` | GET | `/api/v1/admin/platform/users` | Returns DB users OR file store | **Dual persistence** — response structure differs between DB (has `id` as UUID) and file store (has `id` as string) |

---

## 8. Role & Permission Issues

### Three Incompatible Role Systems

| System | File | Roles Defined |
|---|---|---|
| Frontend permissions | `apps/web/src/lib/permissions.ts` | `super_admin`, `admin`, `manager`, `analyst`, `viewer`, `user`, `owner` |
| Frontend RBAC guard | `apps/web/src/components/auth/rbac.tsx` | `super_admin`, `tenant_admin`, `user` |
| Backend RBAC | `apps/api/src/core/rbac.py` | `super_admin`, `owner`, `admin`, `member`, `viewer` |
| Backend User model | `apps/api/src/core/models.py` | `owner`, `admin`, `member`, `viewer` (CheckConstraint) |
| Tenant store | `apps/web/src/stores/tenant-store.ts` | `admin`, `manager`, `member`, `viewer` |
| Billing usage router | `apps/api/src/api/router/admin_platform.py:59` | `member` mapped to `viewer` on line 59 |

### Permission Gaps

- **`rbac.tsx` checks permissions that no role has**: `CanDeleteTender` checks `tender:delete` (no role has it), `CanManageUsers` checks `user:manage` (no role has it), `CanViewAnalytics` checks `analytics:view` (only matches via wildcard for super_admin)
- **`manager` and `analyst` roles are mapped to `member`** in backend `admin_platform.py:135` — losing their distinct permission sets
- **`member` role** in `tenant-store.ts` doesn't exist in `permissions.ts` — frontend permission checks will fail for this role
- **`tenant_admin`** in `rbac.tsx` doesn't exist in `permissions.ts` — role guard checking for `tenant_admin` will always fail in `hasPermission()`
- **Frontend `canAccessTenantDashboard()`** returns false for `super_admin` — super admins are blocked from tenant dashboards
- **Backend `canAccessTenant()`** in `AuthContext` checks `self.tenant_id == tenant_id` — but tenant_id can be None

---

## 9. Database Issues

### Schema Inconsistencies

| Issue | Location |
|---|---|
| `User.role` CheckConstraint allows `owner, admin, member, viewer` but frontend sends `manager, analyst` | `models.py:132`, `admin_platform.py:134` |
| `Tenant.plan` default is `'free'` but CheckConstraint plans are `'free', 'starter', 'professional', 'enterprise'` | `models.py:82` — missing `'free'` in CheckConstraint? Actually it IS there |
| `Tenant` has no `billing_cycle` field but `billing.py:117` sets `tenant.billing_cycle` | `models.py:69-97`, `billing.py:117` |
| `Document` has both `metadata` column alias (`metadata_json`) and `tags/folder` as separate columns — redundant | `models.py:278-281` |
| `AnalysisResult` references `prompt_versions.id` FK but `PromptVersion` exists in same models file — **OK** | `models.py:361` |
| `Bid` has `ai_analysis` (JsonCol) and `ai_score` (Float) but `AnalysisResult` table also stores analysis — **two locations for same data** | `models.py:231-232`, `models.py:349-379` |
| `Proposal` table and `Bid` table overlap in purpose — both store tender responses with amounts, statuses, bidder IDs | `models.py:212-246`, `models.py:433-457` |

### Missing Indexes

| Table | Missing Index | Impact |
|---|---|---|
| `users` | `idx_user_email_verified`, `idx_user_last_login` | Slow user filtering by email_verified, last_login_at |
| `tenants` | `idx_tenant_plan`, `idx_tenant_created` | Slow tenant queries by plan or date range |
| `bids` | `idx_bid_tenant_id` | No tenant isolation index on bids |
| `proposals` | `idx_proposal_bidder`, `idx_proposal_tenant` | No indexes for bidder or tenant queries |
| `queue_jobs` | `idx_queue_tenant_created`, `idx_queue_tenant_status` | Slow tenant-scoped job queries |
| `subscriptions` | `idx_sub_tenant_plan`, `idx_sub_tenant_status` | No tenant-specific subscription indexes |
| `notifications` | `idx_notification_tenant_created` | No tenant-scoped notification queries |

### Missing Relations

| Missing Relationship | Models Involved | Impact |
|---|---|---|
| `Bid` → `Tenant` (direct) | `Bid` has `tenant_id` via `TenantMixin` but no `tenant` back_populates | Cannot eager-load tenant from bid |
| `Proposal` → `User` (direct) | `Proposal` has `bidder_id` FK to `users` but no `user` relationship | Cannot eager-load user from proposal |
| `Subscription` → `Tenant` (direct) | `Subscription` has `tenant_id` but no `tenant` relationship, no `back_populates` on `Tenant` | Cannot navigate subscription↔tenant |
| `QueueJob` → `User` | `QueueJob` has no `user_id` — cannot track which user triggered which job | No audit trail for background jobs |

---

## 10. Deployment Risks

### Environment Configuration

| Risk | Details |
|---|---|
| **Placeholder Clerk keys in `.env.local`** | `pk_test_placeholder` and `sk_test_placeholder` — production will fail if Vercel env vars aren't set |
| **Super Admin credentials in `.env`** | `SUPER_ADMIN_PASSWORD=SuperAdmin@123` and `SUPER_ADMIN_EMAIL=admin@tenderiq.com` committed to repo |
| **Database URL with default credentials** | `root:root@localhost:3306` in `config.py` as default |
| **JWT secret is a dev placeholder** | `dev-secret-change-in-production-min-32-chars` — will work in dev but insecure in production |
| **`NEXT_PUBLIC_API_URL` fallback to localhost** | 6+ files use `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'` — production traffic could hit localhost if env var missing |
| **No `.env` validation at deploy time** | `validate-env.ps1` runs in CI but not during actual deployment |
| **Python dependency version drift** | `requirements.txt` and `package.json` have 8+ mismatched dependency versions; which is source of truth is unclear |

### Missing Configs

| File | Status | Impact |
|---|---|---|
| `Dockerfile` | Missing | Referenced in `deploy.yml` but doesn't exist; Railway falls back to Nixpacks |
| `docker-compose.yml` | Missing | No local production-like environment |
| `.dockerignore` | Missing | Bloated Docker builds |
| `LICENSE` | Missing | README says MIT but no license file |
| `nginx.conf` | Missing | No reverse proxy config for production API |
| `sentry.yml` | Missing | Sentry DSN is configured but no Sentry init in `main.py` |

### CI/CD Pipeline

| Issue | File | Impact |
|---|---|---|
| Uses `npm install` instead of `pnpm install` | `ci.yml:15` | All CI jobs fail — cannot resolve workspace deps |
| Lint/typecheck failures suppressed | `ci.yml:30` | `|| echo "..."` causes CI to pass even when linting fails |
| Backend deploy disabled | `deploy.yml:33` | `if: false` — API is never deployed |
| Integration tests are placeholders | `automated-tests.yml:40` | Just `echo "passed"`, no actual test execution |
| E2E tests reference non-existent scripts | `automated-tests.yml:55` | `pnpm preview` and `pnpm --filter @tendoriq/web e2e` don't exist |
| Vercel deploy uses third-party action | `deploy.yml:20` | `amondnet/vercel-action@v25` — supply chain risk |
| No staging environment | `deploy.yml` | Only production deployment defined |
| No rollback procedure | `deploy.yml` | Failed deploy has no rollback step |
| Security scan uses deprecated tools | `production-ready.yml:15` | `safety` and `bandit` checks may fail on outdated DB |

### Package / Dependency Risks

| Risk | Details |
|---|---|
| `framer-motion ^12.39.0` | Stable framer-motion is v11.x; v12 may not exist — likely typo or incompatible version |
| `zustand ^5.0.3` | Zustand is at v4.x; v5 may not be available |
| `paddleocr` and `paddlepaddle` (~2GB) included for all environments | Even local dev must download 2GB of ML dependencies |
| `sonner ^1.7.3` | May be stale or invalid version |
| `vitest ^2.1.8` with `@vitejs/plugin-react ^4.3.4` | Compatibility not verified |
| No `aioboto3` dependency | `StorageService` uses synchronous `boto3` in async context — blocks event loop |
| `redis`, `arq`, `asyncpg` removed from deps | `documentation still references` ARQ queue and Redis, but they're removed |
