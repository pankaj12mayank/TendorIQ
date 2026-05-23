# TenderIQ — End-to-End Audit Report & Fix Plan

**Project:** `tendoriq`  
**Audit date:** 2026-05-22  
**Status tracking:** [docs/AUDIT_STATUS.md](docs/AUDIT_STATUS.md)

---

## Layer completion summary

| Layer | Issues | Fixed | Status |
|-------|--------|-------|--------|
| **L1** | **6** | **6** | **Completed 100%** |
| **L2** | **7** | **7** | **Completed 100%** |
| **L3** | **7** | **7** | **Completed 100%** |
| **L4** | **6** | **6** | **Completed 100%** |
| **L5** | **7** | **7** | **Completed 100%** |
| **L6** | **7** | **7** | **Completed 100%** |
| **L7** | **7** | **7** | **Completed 100%** |
| **L8** | **7** | **7** | **Completed 100%** |
| **L9** | **6** | **6** | **Completed 100%** |
| L10–L35 | See below | — | **Completed 100%** |

---

# Layer 1 — Repository & documentation integrity ✅

**Issue count: 6 · Fixed: 6 · Layer 1 completed 100%**

| ID | Severity | Finding | Fix applied |
|----|----------|---------|-------------|
| L1-1 | Info | `FIX_PLAN.md` claimed all issues fixed; misleading | Canonical report is this file; `FIX_PLAN.md` removed / not restored |
| L1-2 | Med | `architecture.md` described PostgreSQL + Redis | Rewrote `docs/architecture.md` for MySQL + in-process queue |
| L1-3 | Med | Old QA/readiness docs overstated production readiness | Banners + checklist updates in `qa-production-audit.md`, `production-readiness_report.md` |
| L1-4 | Med | README API base `/v1` vs `/api/v1` | README base URLs and metrics path corrected |
| L1-5 | Low | Package name `tendermonorepo` | Renamed to `tenderiq` in `package.json` and `pyproject.toml` |
| L1-6 | Info | Remove `AGENTS.md`, `FIX_PLAN.md` | Files absent; policy in `docs/AUDIT_STATUS.md` |

---

# Layers 2–35 — Findings (pending)

> Fix work continues layer-by-layer starting at **L2**. Details unchanged from audit; see phased plan at end.

## Layer 2 — Role model (DB vs JWT) ✅

**Issue count: 7 · Fixed: 7 · Layer 2 completed 100%**

| ID | Fix applied |
|----|-------------|
| L2-1 | Platform `super_admin` not stored on `users.role`; documented in models + `docs/ROLES.md` |
| L2-2 | `ensure_demo_account()` + JWT `tenant_id` / `membership_role` on demo login |
| L2-3 | `membership_role` in JWT payload, `AuthContext`, `get_current_user`, `/auth/me` |
| L2-4 | `core/roles.py` normalizes `tenant_admin`; RBAC alias; API `UserRole` cleaned |
| L2-5 | Admin `_map_db_user` uses membership role from DB |
| L2-6 | Shared types: `membershipRoleSchema`, `platformRoleSchema` |
| L2-7 | Tokens + `permissions.ts` alias handling; `owner`/`admin` in design roles |

## Layer 3 — RBAC vocabulary ✅

**Issue count: 7 · Fixed: 7 · Layer 3 completed 100%**

| ID | Fix applied |
|----|-------------|
| L3-1 | `packages/shared/permissions.json` uses API enum strings (`tender:update`, etc.) |
| L3-2 | Removed `*:write` permissions; `PERMISSION_ALIASES` maps write → update/create |
| L3-3 | `rbac.tsx` uses shared `hasPermission`; duplicate matrix removed |
| L3-4 | Login + `/auth/me` return permissions; FE uses server list first |
| L3-5 | Shared + API alias resolution for permission checks |
| L3-6 | Viewer row excludes `analytics:view` |
| L3-7 | Member row matches API `ROLE_PERMISSIONS` |

## Layer 4 — API RBAC enforcement ✅

**Issue count: 6 · Fixed: 6 · Layer 4 completed 100%**

| ID | Fix applied |
|----|-------------|
| L4-1 | `api/dependencies/rbac_deps.py` + `require_tenant_permission` on tenant routers |
| L4-2 | CRUD mapped to `Permission` enum per route (tender/document/AI/export) |
| L4-3 | Removed non-functional decorators from `core/rbac.py` |
| L4-4 | Super-admin blocked on tenant APIs; platform routes unchanged |
| L4-5 | `permissions.py` service helpers retained for layer 8+ |
| L4-6 | `auth.require_permission` → `require_tenant_permission` |

## Layer 5 — Frontend RBAC & navigation ✅

**Issue count: 7 · Fixed: 7 · Layer 5 completed 100%**

| ID | Fix applied |
|----|-------------|
| L5-1 | Permission guards on create-tender CTAs (`rbac.tsx` → dashboard/tenders) |
| L5-2 | `getPostLoginPath` covers all tenant membership roles |
| L5-3 | `X-Tenant-ID` on API client + auth fetch helpers |
| L5-4 | `getMembershipRole` for matrix checks; `AuthUser.membershipRole` persisted |
| L5-5 | Sidebar items gated by `hasPermission` per href |
| L5-6 | `ProtectedRoute.requiredPermission`; tenant analytics → `/dashboard/usage` |
| L5-7 | Layout blocks super_admin on tenant shell; login/me store tenant context |

## Layer 6 — Local JWT auth ✅

**Issue count: 7 · Fixed: 7 · Layer 6 completed 100%**

| ID | Fix applied |
|----|-------------|
| L6-1 | Demo/DB JWT always carries `tenant_id`; status documents super_admin exception |
| L6-2 | `_login_user_payload` + `/me` expose `id`/`user_id`; name from DB when available |
| L6-3 | `/auth/status` — configuration flags only, no PII |
| L6-4 | Removed invalid-password + Bearer header fake success path |
| L6-5 | JWT `jti` revocation on `POST /auth/logout` |
| L6-6 | FE session uses API user UUID, not email fallback |
| L6-7 | `getAuthToken()` centralizes token read for API client |

## Layer 7 — Clerk vs local auth ✅

**Issue count: 7 · Fixed: 7 · Layer 7 completed 100%**

| ID | Fix applied |
|----|-------------|
| L7-1 | Conditional middleware — local JWT mode bypasses Clerk `protect()` |
| L7-2 | `clerk-env.ts` drives middleware + `AppClerkProvider` + `AuthProvider` |
| L7-3 | `clerk_bootstrap.py`, `/auth/clerk/session`, webhooks sync users |
| L7-4 | `ClerkAuthProvider` + `sign-in-clerk` align redirects with local auth |
| L7-5 | Sign-up page documents Clerk vs credential onboarding |
| L7-6 | `api-client` 401 → `/sign-in` for admin paths |
| L7-7 | Webhook guards missing secret; bootstraps on create/update |

## Layer 8 — Tenant middleware ✅

**Issue count: 7 · Fixed: 7 · Layer 8 completed 100%**

| ID | Fix applied |
|----|-------------|
| L8-1 | `AuthMiddleware` + `auth_resolver.py`; `get_current_user` reuses `request.state.auth` |
| L8-2 | `resolve_tenant_id` (strict) vs `get_optional_tenant_id`; single `get_current_tenant_id` |
| L8-3 | Header tenant validated via `verify_tenant_access` |
| L8-4 | `tenant_paths.py` scoped vs exempt prefixes |
| L8-5 | JWT `tenant_id` bound to `request.state.tenant_id` |
| L8-6 | `tenant_utils.parse_tenant_uuid` on analysis API |
| L8-7 | Rate-limit Redis warning when disabled |

## Layer 9 — Session sync ✅

**Issue count: 6 · Fixed: 6 · Layer 9 completed 100%**

| ID | Fix applied |
|----|-------------|
| L9-1 | `build_me_response` always returns matrix permissions |
| L9-2 | FE restore: refresh retry; no viewer downgrade on offline |
| L9-3 | Super-admin `permissions` include `all` + enum strings |
| L9-4 | `/me` includes `name` from DB |
| L9-5 | `issue_session_tokens` unifies JWT creation |
| L9-6 | Login + refresh token stored in `auth-session` |

## Layer 10 — Platform admin — 5 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L10-1 | Super-admin routing / API guard | `getPostLoginPath` → `/dashboard/admin`; `SuperAdmin` on `/admin/platform/*` |
| L10-2 | Super-admin cannot use tenant APIs without tenant | `PlatformScopeBanner` on admin console |
| L10-3 | Mock queue/AI metrics in admin APIs | `core/platform_metrics.py` aggregates `QueueJob`, `UsageLog`, email queue |
| L10-4 | Admin analytics vs tenant dashboard | Platform hook uses `/admin/platform/analytics/summary`; tenant uses billing usage |
| L10-5 | Dual user stores (DB + file) | User list/create/patch/delete are DB-only |

## Layer 11 — Dashboard E2E — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L11-1 | API snake_case vs FE camelCase | `TenderService._tender_to_dict` emits camelCase; `mapTenderFromApi` for legacy |
| L11-2 | Tenders page expected `{ tenders }` | Uses `useTenders()` → `{ data, meta }` |
| L11-3 | Missing `/dashboard/tenders/new` | New create page + `useCreateTender` |
| L11-4 | `organization_id` required on create | Optional; tenant from JWT |
| L11-5 | Single-tender GET envelope mismatch | `unwrapData` in hooks |
| L11-6 | Analysis URL mismatch | `/analysis/tender/{tender_id}` dashboard shape |
| L11-7 | Analysis page no tender context | `?tenderId=` query param |

## Layer 12 — Documents & OCR E2E — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L12-1 | Files API `db` param not injected | `AsyncSession = Depends(get_db)` on all file routes |
| L12-2 | `/documents/folders/list` captured by `/{document_id}` | Static routes moved before dynamic id |
| L12-3 | Folder list missing `Document` import | Import from `core.models` |
| L12-4 | Upload UI sent empty files | Store and upload actual `File` blobs |
| L12-5 | Upload auth / flow reliability | Direct multipart upload with Bearer headers; fallback to signed URL |
| L12-6 | OCR missing tenant RBAC; language body mismatch | `require_tenant_member` + query/body language on process |
| L12-7 | Document GET/PATCH envelope drift | `unwrapDocumentPayload` in document hooks |

## Layer 13 — Billing & usage quotas — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L13-1 | Billing APIs without tenant guard / UUID | `require_tenant_member` + `parse_tenant_uuid` |
| L13-2 | Missing `/billing/quota`, `/usage/summary`, subscription mutations | New routes in `billing.py` |
| L13-3 | FE expected rich subscription/quota shapes | `core/billing/fe_responses.py` |
| L13-4 | `use-billing` wrong paths / no API load | Aligned hooks + billing page `initialize()` |
| L13-5 | `use-usage` called non-existent quota paths | `/billing/quota`, `/billing/usage/summary` |
| L13-6 | Plan id and billing cycle mismatch | `normalize_plan_id`, `annual`→`yearly` |
| L13-7 | AI token usage stubbed at 0 | Sum `UsageLog.tokens_used` per tenant |

## Layer 14 — Email triggers & notifications — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L14-1 | FE called `/email/triggers/*`; API only had `/emails/trigger/*` | Compat router `email_triggers.py` mounted at `/api/v1` |
| L14-2 | Trigger body shape mismatch (`{ user_email, data }` vs flat) | `TriggerRequest` `model_validator` coerces flat payloads |
| L14-3 | Email logs/stats used in-memory `MOCK_LOGS` | `_persist_email_log` writes `email_logs` table |
| L14-4 | `/emails/logs` and `/emails/stats` not tenant-scoped from DB | Query `DbEmailLog` with tenant filter |
| L14-5 | `useNotifications` expected `{ notifications }` | `notifications-api.ts` unwraps `data` + maps fields |
| L14-6 | Missing notification delete endpoint | `DELETE /notifications/{id}` soft-delete |
| L14-7 | Hooks documented as mock-only in system audit | Real API via `api-client`; onboarding paths unchanged (already wired) |

## Layer 15 — Onboarding hardening — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L15-1 | JWT missing `tenant_id` after org creation (steps 2–5 fail tenant middleware) | Step 1 returns `session` tokens with tenant + owner role |
| L15-2 | Completed onboarding still had stale JWT | Step 5 returns refreshed `session` tokens |
| L15-3 | `/onboarding/status` empty state missing required timestamps | Default `created_at` / `updated_at` on new-user response |
| L15-4 | FE `plan_pro` / `annual` rejected by onboarding schema | Onboarding plan alias map + billing cycle normalization |
| L15-5 | Zustand persist could disagree with server progress | `mapOnboardingState` + full sync after each step and on load |
| L15-6 | Step 4 duplicated plan catalog vs API | `fetchPlans()` drives Step 4 UI |
| L15-7 | `syncFromServer` omitted `tenantName` | Store sync includes org name from step 1 data |

## Layer 16 — Export E2E — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L16-1 | `get_current_user` missing in export router | Import + auth on download |
| L16-2 | `/{export_id}/download` shadowed `/history`, `/formats` | Download route moved to end of router |
| L16-3 | FE `/export/risk_analysis/` vs API `risk-analysis` | Path map + compat route |
| L16-4 | Entity export responses not parsed on FE | `export-api.ts` `parseExportJob` |
| L16-5 | Analysis export was mock `setTimeout` + JSON blob | `exportTenderReport` + server-side generators |
| L16-6 | `organization_id='default'` without tenant | `_tenant_org_id` guard |
| L16-7 | Export history / audit export shape drift | `mapHistoryRow`; audit export csv/json only |

## Layer 17 — Observability — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L17-1 | Uptime used fixed `MOCK_START_TIME` | `observability_metrics.set_app_start_time()` on API boot |
| L17-2 | Metrics with `tenant_id=None` returned empty/wrong data | `require_tenant_member` + `_tenant_uuid` on metrics routes |
| L17-3 | Summary always showed 0% failure/processing | DB-backed `build_tenant_metrics_summary` |
| L17-4 | Observability logic scattered / untested | `core/observability_metrics.py` module |
| L17-5 | No tenant FE hook for `/observability/*` | `use-observability` on usage dashboard |
| L17-6 | Duplicate opaque health endpoints | Canonical `/health` noted; detailed health probes DB |
| L17-7 | Admin analytics export claimed PDF but saved JSON | csv/json export; error state on `use-analytics` |

## Layer 18 — Enterprise SSO — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L18-1 | SSO config stored in-memory on `SSOService` | `tenant_store.py` persists on `tenants.settings['sso']` |
| L18-2 | Configure routes used legacy `admin`/`super_admin` string checks | `RequireOrgUpdate` / `RequireSettingsRead` RBAC deps |
| L18-3 | No org-scoped public session exchange for IdP tokens | `POST /sso/session` + `bootstrap.exchange_sso_session` |
| L18-4 | Public SSO routes blocked by tenant middleware | Exempt `/sso/session` and `/sso/public/` in `tenant_paths.py` |
| L18-5 | No FE SSO client or sign-in org slug flow | `sso-api.ts`, `use-sso.ts`, `/sign-in?org=` + profile status card |
| L18-6 | SSO groups not mapped to membership permissions | `GROUP_TO_MEMBERSHIP` + `permissions_for_role` in `SSOHandler` |
| L18-7 | Enterprise SSO untested / always on | `FEATURE_SSO` gate; `test_layer18_sso.py` + `sso-api.test.ts` |

## Layer 19 — API response consistency — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L19-1 | Paginated lists put `total`/`page` at JSON root | `create_paginated_response` on notifications + analysis |
| L19-2 | Billing reads returned bare objects | `create_response` on subscription/quota/summary; dual `plans` key |
| L19-3 | `HTTPException` returned FastAPI `{detail}` only | Global handler → `create_error_response` envelope |
| L19-4 | FE `api-client` ignored nested validation errors | `parseApiErrorMessage` / `parseApiErrorCode` in `api-envelope.ts` |
| L19-5 | Hooks could not parse legacy pagination | `parsePaginated` reads root `page`/`limit`/`total` fallback |
| L19-6 | Billing hooks assumed non-envelope shapes | `parsePlansResponse`, invoice/payment parsers + unwrap |
| L19-7 | Envelope helpers untested | `test_layer19_api_consistency.py` + `api-envelope.test.ts` |

## Layer 20 — Frontend data fetching — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L20-1 | Mix of `api` client vs raw `fetch` without base URL/auth | `api-config.ts` + `authenticatedFetch` with session headers |
| L20-2 | Analysis store used relative unauthenticated `fetch` | `analysis-api.ts`; store `refreshAnalysis(tenderId)` via client |
| L20-3 | Duplicate analysis fetch logic in hook vs store | Shared `fetchTenderAnalysis` / `patchTenderAnalysisField` |
| L20-4 | Export download / uploads duplicated API URL + auth | `authenticatedFetch`; 120s upload timeout constant |
| L20-5 | Auth/Clerk/onboarding scattered `NEXT_PUBLIC_API_URL` | `apiUrl()` / `resolveApiUrl()` across auth flows |
| L20-6 | React Query errors easy to miss (`throwOnError: false`) | `getQueryErrorMessage`, `errorMessage` on tender hooks, `retry: 1` |
| L20-7 | Fetch helpers untested | `test_layer20_fe_fetching.py` + `api-fetch.test.ts` |

## Layer 21 — UI routes & dead links — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L21-1 | `/dashboard/tenders/new` linked but missing (historical) | Create page exists; `ROUTES.tenderNew` canonical |
| L21-2 | `/admin/sign-in` vs `/admin/login` drift | `/admin/sign-in` + `/admin/login` redirect to `ROUTES.signIn` |
| L21-3 | `/` vs `/landing` public path inconsistency | `/landing` → `/`; middleware + `isPublicAppPath` aligned |
| L21-4 | Sidebar `/dashboard/organizations` 404 | Organizations page + `organizations-api.ts`; API `func` import |
| L21-5 | Review nav `/dashboard/review` 404 | Nav → `/dashboard/tenders/review`; legacy redirect page |
| L21-6 | `/dashboard/notifications` missing | Notifications page; bell in header loads API list |
| L21-7 | Dead links untested | `routes.ts`, sitemap, 404 helpers; layer 21 tests |

## Layer 22 — Dashboard UX & loading — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L22-1 | Dashboard blocked on onboarding check with generic loading | Contextual boot messages + `DashboardBootLoading` chrome |
| L22-2 | Slow/failed onboarding API could hang dashboard forever | 8s timeout fail-open; errors allow access |
| L22-3 | `RoleGuard` / `PermissionGuard` returned `null` while loading | `GuardLoadingPlaceholder` pulse skeleton |
| L22-4 | Sidebar `layoutId` motion ignored reduced-motion preference | `useReducedMotion` + `sidebarLayoutTransition` |
| L22-5 | Empty Suspense sidebar fallback | `SidebarSkeleton` + segment `loading.tsx` |
| L22-6 | `GuestRoute` blank screen during auth redirect | `LoadingState` “Redirecting…” |
| L22-7 | Dashboard home table spinner-only loading | `TableRowSkeleton` rows while tenders load |

## Layer 23 — Admin modules — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L23-1 | `RealtimeQueueStatus` / `RealtimeMetrics` used hardcoded/random data | Props from `useRealtimeMetrics` + DB `queueStats` / analytics summary |
| L23-2 | `SystemHealth` static mock components | `platform_system_health` + `SystemHealth` wired on analytics tab |
| L23-3 | Admin API parsing scattered in hooks | `admin-platform-api.ts` parsers + `unwrapData` |
| L23-4 | `use-admin.ts` assumed raw response shapes | Uses `parsePlatformUsersResponse`, queue, providers, failed jobs |
| L23-5 | Queue cancel/pause/resume routes missing | `POST /admin/platform/queue/jobs/{id}/cancel|pause|resume` |
| L23-6 | Audit logs tenant-only / wrong path for super admin | `GET /admin/platform/audit-logs` + FE route switch |
| L23-7 | `MOCK_ROLES` disconnected from permission matrix | `ADMIN_ROLE_OPTIONS` from `ROLE_PERMISSIONS_MATRIX` |

## Layer 24 — Shared package — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L24-1 | `tenderSchema` used `organizationId` vs API `tenant_id` | `tenantId` required; `organizationId` optional deprecated |
| L24-2 | Tender mappers duplicated in web only | `@tendoriq/shared/tenders` (`mapTenderFromApi`, `mapTenderToApi`, formatters) |
| L24-3 | `api-envelope` owned tender mapping | Re-exports shared tender helpers; `use-api` uses `ClientTender` |
| L24-4 | `.env.example` keys not aligned with shared `env.ts` | `FRONTEND_URL`/`API_URL` aliases, dev JWT default, `NEXT_PUBLIC_FEATURE_*` |
| L24-5 | Feature flags defined but not consumed in web | `feature-flags-client.ts` + `lib/feature-flags.ts` |
| L24-6 | API prefix duplicated ad hoc | `API_ROUTE_PREFIX` in shared constants; `api-config` uses it |
| L24-7 | SSO / advanced analytics always visible | Sidebar, sign-in `?org=`, profile SSO gated by flags |

## Layer 25 — Database & migrations — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L25-1 | Docs claimed `create_all` on API startup | `docs/MYSQL_SETUP.md` + `docs/database-migrations.md`; `init_db` only pings DB |
| L25-2 | Alembic first revision only created 2 admin tables | `20260522_admin_store` runs `Base.metadata.create_all` for full schema |
| L25-3 | `layer1` migration failed on DBs that already had columns | Idempotent `migration_utils` + conditional index/column ops |
| L25-4 | `alembic.ini` URL misleading vs runtime | Comment + `env.py` uses `settings.database_url_sync` |
| L25-5 | Tender list/delete ignored `deleted_at` | `BaseRepository` filters active rows; soft delete on delete |
| L25-6 | No documented migrate command | `pnpm --filter @tendoriq/api run db:migrate` / `alembic upgrade head` |
| L25-7 | Admin store models overlapped partial migration | Single metadata migration includes `AIProvider` + `DismissedFailedJob` |

## Layer 26 — Security (beyond RBAC) — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L26-1 | Any tenant member could mutate all tenders | `row_access.py` + `TenderService._assert_can_modify` (owner/admin/manager vs creator) |
| L26-2 | Document delete lacked owner checks | `uploaded_by_id` in metadata; row check on files/documents DELETE |
| L26-3 | CORS allowed `*` methods/headers | Explicit allow-lists in settings + `main.py` |
| L26-4 | 500 responses could leak exception text | `expose_error_details` / dev-only `detail`; always `request_id` |
| L26-5 | Production security headers incomplete | HSTS + CSP on API responses when `is_production` |
| L26-6 | No centralized row-access policy module | `core/row_access.py` + unit tests |
| L26-7 | `.env.example` missing CORS/security flags | Documented `CORS_*` and `EXPOSE_ERROR_DETAILS` |

## Layer 27 — Testing & CI — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L27-1 | API tests mostly health-only / no contract coverage | `test_openapi_contract.py` + tenant auth integration tests |
| L27-2 | Playwright `example.spec.ts` only | `e2e/public-routes.spec.ts` route matrix + auth redirect |
| L27-3 | No FE↔BE path contract | `tests/contracts/fe_api_paths.json` + Vitest `api-contract.test.ts` |
| L27-4 | Main `ci.yml` skipped API pytest | `test-api` job runs `pytest tests/unit tests/integration` |
| L27-5 | Hooks/stores untested | `lib/query-error-message.ts` + Vitest unit tests (re-exported from `use-api`) |
| L27-6 | Integration health test broken import | Fixed `test_health.py`; `tests/conftest.py` env defaults |
| L27-7 | `organizations.py` syntax error blocked app import | Fixed docstring; [docs/testing.md](docs/testing.md) |

## Layer 28 — Monorepo & tooling — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L28-1 | API excluded from pnpm workspace / inconsistent filters | `apps/*` workspace; scoped `@tendoriq/*` in root scripts and CI |
| L28-2 | CI mixed `npm` and short `web` filters | `ci.yml` uses `pnpm` + `@tendoriq/web` throughout |
| L28-3 | E2E workflow called missing `pnpm preview` | Web `preview` script; `automated-tests.yml` starts preview before Playwright |
| L28-4 | `production-ready` required live secrets + checked `dist/` | Validates `.env.example`; asserts `apps/web/.next` after build |
| L28-5 | `rm -rf` clean scripts fail on Windows | Shared package `clean` via Node; documented in monorepo guide |
| L28-6 | Docker build lacked ignore rules | `apps/api/.dockerignore`; Dockerfile comment on requirements source |
| L28-7 | Dual API client confusion | `@/lib/api` re-export shim + [docs/monorepo-tooling.md](docs/monorepo-tooling.md) |

## Layer 29 — Email system (enterprise) — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L29-1 | Reset endpoint consumed token without updating password | `PasswordResetService.apply_new_password` + bcrypt in `core/passwords.py` |
| L29-2 | DB users could not use password set via reset at login | `auth/login` verifies `preferences.password_hash` when set |
| L29-3 | Docs referenced ARQ/Redis worker | [docs/EMAIL_SYSTEM.md](docs/EMAIL_SYSTEM.md) describes inline `email_process` |
| L29-4 | Missing email encryption env in template | `ENCRYPTION_KEY`, `EMAIL_*` in `.env.example` |
| L29-5 | FE↔API contract omitted email admin paths | Extended `fe_api_paths.json` |
| L29-6 | Email seed failures only warned | Development startup logs migration hint on seed error |
| L29-7 | Sign-in had no forgot-password link | Link on sign-in page; reset/forgot pages wired to API |

## Layer 30 — Audit logs — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L30-1 | Tenant audit API returned empty user fields | `audit_log_to_dict` + `load_users_by_id` |
| L30-2 | Audit routes lacked RBAC | `RequireAnalyticsView` on `/api/v1/audit/*` |
| L30-3 | Platform list `total` was page size only | `func.count` + filter query params |
| L30-4 | Super-admin export hit tenant-only `/audit/export` | `POST /admin/platform/audit-logs/export` |
| L30-5 | `log_action` calls omitted required `action_type` | Default + fixes in permissions/safe-access |
| L30-6 | No audit on login or tender delete | `_audit_tenant_login`, `tenant_audit.log_delete` |
| L30-7 | Admin audit UI hooks bug + missing diff state | Fixed component order; map old/new values |

## Layer 31 — File storage — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L31-1 | Signed URL helpers called without `await` | Awaited in files, documents, OCR, parsing, worker |
| L31-2 | `local` provider still required boto3 | Filesystem backend under `STORAGE_LOCAL_PATH` |
| L31-3 | Sync boto3 blocked event loop | `asyncio.to_thread` wrapper retained for S3/R2 |
| L31-4 | Local dev could not complete presigned PUT flow | HMAC tokens + `/api/v1/files/blob/{key}` |
| L31-5 | Cross-tenant storage key access possible | `assert_tenant_storage_key` on sensitive routes |
| L31-6 | OCR/parsing used HTTP for all backends | `read_file()` fast-path when `is_local` |
| L31-7 | Env/docs drift (`STORAGE_TYPE`) | `STORAGE_PROVIDER` in `.env.example`; [docs/storage.md](docs/storage.md) |

## Layer 32 — Type drift — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L32-1 | Admin `UserRole` omitted `owner` / `member` | `@tendoriq/shared/roles` + `AdminConsoleRole` |
| L32-2 | Duplicate plan normalization in web only | `@tendoriq/shared/plans`; billing bridge re-exports |
| L32-3 | Onboarding `plan_pro` / `annual` vs Zod enum | `step4Schema` uses shared transforms |
| L32-4 | Notification mapper only in web | `@tendoriq/shared/notifications` |
| L32-5 | `AuthUser` duplicated session shape | `@tendoriq/shared/auth` `SessionUser` |
| L32-6 | No documented type ownership | [docs/type-drift.md](docs/type-drift.md) |
| L32-7 | Drift regressions untested | `test_layer32_type_drift.py`, `shared-type-drift.test.ts` |

## Layer 33 — Audit coverage — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L33-1 | Tender create/update not audited | `_audit_tender_mutation` on POST/PATCH |
| L33-2 | Document mutations under-logged | Audit on upload complete + delete |
| L33-3 | Platform export fetched unbounded rows | `clamp_export_limit` + `.limit()` |
| L33-4 | Tenant export unbounded | `AuditExportRequest.limit` + cap |
| L33-5 | Admin UI hardcoded `limit: 100` | `audit-constants.ts` shared with API |
| L33-6 | Tender delete audit swallowed errors | Warning log via `_audit_tender_mutation` |
| L33-7 | No coverage doc/tests | [docs/audit-coverage.md](docs/audit-coverage.md), `test_layer33_audit_coverage.py` |

## Layer 34 — Storage paths & signed URLs — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L34-1 | `./uploads` depended on process CWD | `resolve_storage_local_path` anchored to `apps/api` |
| L34-2 | Windows/Linux path drift for relative env | Settings validator stores absolute `STORAGE_LOCAL_PATH` |
| L34-3 | Client re-resolved path inconsistently | `resolved_storage_local_path` property |
| L34-4 | Local upload dir missing on fresh clone | `ensure_local_storage_root()` in API lifespan |
| L34-5 | Blob token rejected at expiry boundary | `STORAGE_TOKEN_CLOCK_SKEW_SECONDS` on verify |
| L34-6 | Docs/env silent on path + skew | `docs/storage.md`, `.env.example` |
| L34-7 | Regressions untested | `test_layer34_storage_paths.py` |

## Layer 35 — Remaining type drift — 7 issues (completed)

| ID | Issue | Fix |
|----|-------|-----|
| L35-1 | `use-api` Tender type drift | Re-export `ClientTender`; mappers from `@tendoriq/shared/tenders` |
| L35-2 | UI `deadline`/`value` vs API `closingDate`/`budget` | Shared formatters + `ClientTender` fields on tender cards |
| L35-3 | Strict analysis Zod rejected API JSON | `@tendoriq/shared/analysis` loose schema |
| L35-4 | `keyFindings` vs `keyHighlights` mismatch | `analysis-mapper.ts` normalizes sections |
| L35-5 | `mandatory_docs` / partial sections broke parse | Mapper defaults + alias handling |
| L35-6 | Widespread optional `tenant_id` | `tenant_types.py`, UUID validation in `require_tenant_member` |
| L35-7 | Untested drift | `test_layer35_type_drift.py`, Vitest mapper tests |

**All 35 code layers complete.** Operational sign-off requires [reliability gates](#reliability-gates-mandatory) below.

---

# System reliability & root causes

> **Honest gap:** Layers L1–L35 were closed using **static/file tests** and targeted fixes. They did **not** originally require `import app`, `compileall`, or `tenderiq-start.ps1` health checks. That is why the app could show “audit 100%” while **`run.bat` / startup still failed**.

## Reliability gates (mandatory)

| Gate | Command | Pass criteria |
|------|---------|---------------|
| **G1 Compile** | `cd apps/api && python -m compileall -q src` | Exit 0 |
| **G2 Import** | `DOTENV_PATH=<repo>/.env python scripts/verify_import.py` (from `apps/api`) | Prints `OK TenderIQ` |
| **G3 Deps** | `pip install -r requirements.txt` when `requirements.txt` hash changes | All imports in G2 succeed |
| **G4 Stack** | `scripts/tenderiq-start.ps1` | `/health` → `healthy`, frontend HTTP &lt; 500 |
| **G5 DB** | MySQL up + `alembic upgrade head` | Login / tenders list returns data |

Methodology: [docs/audit-methodology.md](docs/audit-methodology.md)

## Root-cause register (startup / E2E failures)

| RC-ID | Symptom | Root cause | Why layer audit missed it | Fix | Gate |
|-------|---------|------------|---------------------------|-----|------|
| **RC-01** | `DATABASE_URL` / `JWT_SECRET` validation error on import | `_PROJECT_ROOT` in `config.py` pointed at `apps/` not repo root; `.env` never loaded | No test imported `Settings()` with real `.env` | `parents[4]` + `get_settings()` fallback path | G2 |
| **RC-02** | `ModuleNotFoundError: svix` | Venv created once; start script skipped `pip install` when venv existed | Layer tests don’t install or import full app | Requirements hash stamp + reinstall in `tenderiq-start.ps1` | G3, G2 |
| **RC-03** | `SyntaxError: non-default argument follows default argument` | FastAPI routes put `RequireAnalyticsView` / `RequireApiAccess` **after** `Query(...)` parameters | Static tests never `compileall` routers | Reordered params in `audit.py`, `export.py`, `sso.py` | G1, G2 |
| **RC-04** | `SyntaxError` in `audit.py` `log_action` | `action_type=` default before required `resource_type` | Same as RC-03 | Swapped parameter order in `dependencies/audit.py` | G1 |
| **RC-05** | `SyntaxError` in `admin_auth.py` | UTF-8 BOM + escaped `\"\"\"` docstrings | File not compiled in CI | Cleaned docstrings / BOM | G1 |
| **RC-06** | `ImportError: permissions_for_role from rbac` | SSO imported symbol from `core.rbac` but implementation lives in `core.local_auth` | `test_layer18` only checked string presence in SSO file | Import from `local_auth` | G2 |
| **RC-07** | “Audit complete” but E2E broken | **Process:** closure = 7/7 static items, not gates G1–G5 | Methodology gap | This section + `audit-methodology.md` | All gates |

## Systemic root cause (meta)

**Treatment of audit as documentation/checklist instead of runnable system verification.**

| Desired state | Current guard |
|---------------|---------------|
| Every merge blocks on import | `apps/api/scripts/verify_import.py` + G2 in start script |
| No silent skip of dependencies | `venv/.requirements.sha256` in `tenderiq-start.ps1` |
| Root causes tracked | Table above + RC-ID in future layer notes |

## E2E smoke paths (manual until Playwright matrix exists)

| # | Flow | Steps | Depends on |
|---|------|-------|------------|
| E2E-1 | Health | `GET /health` | G2 |
| E2E-2 | Demo login | Sign in with `DEMO_USER_*` from `.env` | MySQL, migrations |
| E2E-3 | Tenders | Dashboard → Tenders list → open analysis | JWT `tenant_id`, G4 |
| E2E-4 | Create tender | `/dashboard/tenders/new` → save | RBAC `tender:create` |
| E2E-5 | Document upload | Upload on tender (direct or presign) | Storage provider, quotas |
| E2E-6 | Super admin | `/admin` with `SUPER_ADMIN_*` | Platform routes |

Layer **L27** added CI/tests but not **G2 import** on every PR — recommend adding `verify_import.py` to `.github/workflows/ci.yml`.

---

# Master fix plan (phased)

## Phase 0 — Unblock E2E (next: L2–L8, L11, L16, L17)

JWT `tenant_id`, `X-Tenant-ID`, Clerk middleware conditional, tenders/analysis/billing/email path alignment.

## Phase 1 — RBAC enforcement + real admin metrics

## Phase 2 — Docs/codegen/hardening

---

*Last updated: Layer 35 code complete; reliability gates and root-cause register added (2026-05-23).*
