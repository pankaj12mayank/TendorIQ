# TenderIQ — Audit remediation status

**Canonical report:** [AUDIT_REPORT.md](../AUDIT_REPORT.md)  
**Superseded:** `FIX_PLAN.md`, `AGENTS.md` (removed; do not recreate)

Track fixes by audit layer. **Issue count = fixed count** per layer when marked complete.

| Layer | Title | Issues | Fixed | Status |
|-------|--------|--------|-------|--------|
| L1 | Repository & documentation | 6 | 6 | **Completed 100%** |
| L2 | Role model (DB vs JWT) | 7 | 7 | **Completed 100%** |
| L3 | RBAC permission vocabulary | 7 | 7 | **Completed 100%** |
| L4 | API RBAC enforcement | 6 | 6 | **Completed 100%** |
| L5 | Frontend RBAC & navigation | 7 | 7 | **Completed 100%** |
| L6 | Authentication (local JWT) | 7 | 7 | **Completed 100%** |
| L7 | Clerk vs local auth | 7 | 7 | **Completed 100%** |
| L8 | Tenant middleware | 7 | 7 | **Completed 100%** |
| L9 | Auth /me & session | 6 | 6 | **Completed 100%** |
| L10 | Super admin & platform | 5 | 5 | **Completed 100%** |
| L11 | Tenant dashboard E2E | 7 | 7 | **Completed 100%** |
| L12 | Documents & OCR E2E | 7 | 7 | **Completed 100%** |
| L13 | Billing & usage quotas | 7 | 7 | **Completed 100%** |
| L14 | Email triggers & notifications | 7 | 7 | **Completed 100%** |
| L15 | Onboarding hardening | 7 | 7 | **Completed 100%** |
| L16 | Export E2E | 7 | 7 | **Completed 100%** |
| L17 | Observability | 7 | 7 | **Completed 100%** |
| L18 | Enterprise SSO | 7 | 7 | **Completed 100%** |
| L19 | API response consistency | 7 | 7 | **Completed 100%** |
| L20 | Frontend data fetching | 7 | 7 | **Completed 100%** |
| L21–L35 | See AUDIT_REPORT.md | — | — | Not started |

## Layer 1 — Completed items

| ID | Resolution |
|----|------------|
| L1-1 | `AUDIT_REPORT.md` is source of truth; `FIX_PLAN.md` retired (file absent) |
| L1-2 | `docs/architecture.md` updated for MySQL 8+ and in-process asyncio queue |
| L1-3 | `production-readiness_report.md` and `qa-production-audit.md` disclaimers + stack corrected |
| L1-4 | README API base URLs use `/api/v1` |
| L1-5 | Root `package.json` and `pyproject.toml` renamed to `tenderiq` |
| L1-6 | `AGENTS.md` / `FIX_PLAN.md` not present; policy documented here |

**Layer 1 completed: 6/6 issues fixed (100%).**

## Layer 2 — Completed items

| ID | Resolution |
|----|------------|
| L2-1 | `super_admin` only in JWT/env; documented on `User.role`; not written to DB |
| L2-2 | Demo login bootstraps tenant + JWT `tenant_id` / `membership_role` via `account_bootstrap.py` |
| L2-3 | `membership_role` on JWT, `AuthContext`, `/auth/me`, `get_current_user` |
| L2-4 | `tenant_admin` → `admin` in `roles.py` + RBAC alias; removed enum from API `UserRole` |
| L2-5 | `_map_db_user` uses active `memberships.role`; no member→viewer downgrade |
| L2-6 | Shared `membershipRoleSchema` + platform/membership split in `packages/shared` |
| L2-7 | Design tokens include `owner`/`admin`; `tenant_admin` documented as UI alias |

**Layer 2 completed: 7/7 issues fixed (100%).**

See [ROLES.md](./ROLES.md).

## Layer 3 — Completed items

| ID | Resolution |
|----|------------|
| L3-1 | Canonical strings in `permissions.json` match API `Permission` enum |
| L3-2 | Removed `tender:write` matrix; aliases map `write` → `update` |
| L3-3 | Deleted duplicate `rolePermissions` in `rbac.tsx`; uses `@tendoriq/shared` |
| L3-4 | `/auth/me` + login return server permissions; FE prefers `user.permissions` |
| L3-5 | `hasPermission` alias handling in shared TS + `RBACService.has_permission(str)` |
| L3-6 | `viewer` in JSON has no `analytics:view` (aligned with API) |
| L3-7 | `member` matrix matches API exactly in shared JSON |

**Layer 3 completed: 7/7 issues fixed (100%).**

## Layer 4 — Completed items

| ID | Resolution |
|----|------------|
| L4-1 | `require_tenant_permission` wired on tenders, documents, files, analysis, AI routers |
| L4-2 | Per-action deps: `RequireTenderCreate`, `RequireDocumentDelete`, `RequireAiAnalysis`, etc. |
| L4-3 | Removed broken `request.state.auth` decorators from `core/rbac.py` |
| L4-4 | `admin_platform` + `prompt_mgmt` keep `SuperAdmin`; tenant routes use tenant deps |
| L4-5 | `ProtectedTenantEndpoint` + `check_tenant_and_permission` ready for services |
| L4-6 | `check_permission` + `require_permission` alias to `require_tenant_permission` |

**Layer 4 completed: 6/6 issues fixed (100%).**

## Layer 5 — Completed items

| ID | Resolution |
|----|------------|
| L5-1 | `CanCreateTender` / `PermissionGuard` wired on dashboard + tenders pages |
| L5-2 | `getPostLoginPath` includes `owner`, `member`, `tenant_admin`; unknown → onboarding |
| L5-3 | `X-Tenant-ID` sent via `api-client` + `buildApiAuthHeaders` / `getSessionRequestHeaders` |
| L5-4 | RBAC checks use `membershipRole` (`getMembershipRole`) not conflated with platform role |
| L5-5 | Sidebar nav filtered by permission; `resolveRole` uses membership role |
| L5-6 | `ProtectedRoute` supports `requiredPermission`; analytics routes by role |
| L5-7 | Super-admin redirected from tenant dashboard; session stores `tenantId` + `membershipRole` |

**Layer 5 completed: 7/7 issues fixed (100%).**

## Layer 6 — Completed items

| ID | Resolution |
|----|------------|
| L6-1 | Demo/DB login JWT includes `tenant_id`; super_admin documented as tenant-less |
| L6-2 | Login + `/auth/me` return both `id` and `user_id`; FE prefers UUID fields |
| L6-3 | `/auth/status` exposes flags only (no admin email) |
| L6-4 | Removed fake Clerk `Authorization` login fallback (`role: user`) |
| L6-5 | Logout revokes access token `jti` via `AuthService.revoke_token` |
| L6-6 | Session user `id` from login/me UUID; layout `userId` stable |
| L6-7 | `getAuthToken()` + `getSessionRequestHeaders()` unify cookie/localStorage |

**Layer 6 completed: 7/7 issues fixed (100%).**

## Layer 7 — Completed items

| ID | Resolution |
|----|------------|
| L7-1 | `middleware.ts` skips `clerkMiddleware` when publishable key absent |
| L7-2 | `clerk-env.ts` shared with middleware + `isClerkConfigured()` |
| L7-3 | `POST /auth/clerk/session` + DB bootstrap; `get_current_user` resolves Clerk→membership |
| L7-4 | Clerk provider uses `getPostLoginPath(membershipRole)` + super_admin redirect |
| L7-5 | Sign-up copy clarifies Clerk vs local onboarding path |
| L7-6 | API 401 redirect uses `/sign-in` (not missing `/admin/sign-in`) |
| L7-7 | Clerk webhook requires secret; bootstraps users; `settings` import verified |

**Layer 7 completed: 7/7 issues fixed (100%).**

## Layer 8 — Completed items

| ID | Resolution |
|----|------------|
| L8-1 | `AuthMiddleware` registered; sets `request.state.auth` before `TenantMiddleware` |
| L8-2 | Canonical `resolve_tenant_id` / `get_optional_tenant_id`; `tenant.py` alias kept |
| L8-3 | `X-Tenant-ID` validated against membership when it differs from JWT |
| L8-4 | Tenant required only on `TENANT_SCOPED_PREFIXES`; onboarding/admin exempt |
| L8-5 | Demo JWT `tenant_id` flows through middleware (L2/L6) |
| L8-6 | `parse_tenant_uuid()` on analysis routes — 400 not 500 |
| L8-7 | Rate limit logs when Redis missing instead of silent pass |

**Layer 8 completed: 7/7 issues fixed (100%).**

## Layer 9 — Completed items

| ID | Resolution |
|----|------------|
| L9-1 | `/auth/me` + login return server `permissions` from shared matrix |
| L9-2 | Session restore keeps cached user on network failure; clears only on 401 |
| L9-3 | Super-admin permissions include `all` + full Permission enum strings |
| L9-4 | `/me` returns resolved `name` from DB (L6 helper reused via `build_me_response`) |
| L9-5 | `issue_session_tokens()` — single AuthService path for access + refresh |
| L9-6 | Login returns `refresh_token`, `expires_in`; FE stores and uses `/auth/refresh` |

**Layer 9 completed: 6/6 issues fixed (100%).**

## Layer 10 — Completed items

| ID | Resolution |
|----|------------|
| L10-1 | Super-admin post-login → `/dashboard/admin`; platform routes use `SuperAdmin` dependency |
| L10-2 | `PlatformScopeBanner` explains tenant APIs need membership / `X-Tenant-ID` |
| L10-3 | Admin queue/failed-jobs/analytics use `platform_metrics.py` (DB), not observability mocks |
| L10-4 | `use-analytics.ts` documented as platform-only; tenant usage stays on `/billing/usage/*` |
| L10-5 | Platform user CRUD is DB-only (no `admin_store` file fallback for users) |

**Layer 10 completed: 5/5 issues fixed (100%).**

## Layer 11 — Completed items

| ID | Resolution |
|----|------------|
| L11-1 | Tenders API returns camelCase + `{ success, data, meta }`; FE `api-envelope.ts` unwraps and maps |
| L11-2 | `useTenders` / dashboard home use paginated `data` array (not `{ tenders }`) |
| L11-3 | Added `/dashboard/tenders/new` create form wired to `POST /api/v1/tenders` |
| L11-4 | `TenderCreate.organization_id` optional; tenant from JWT |
| L11-5 | `useTender` / mutations unwrap API envelope |
| L11-6 | Analysis: `GET/PATCH /api/v1/analysis/tender/{id}` + route order before `/{analysis_id}` |
| L11-7 | Analysis page reads `?tenderId=` and calls `useAnalysisApi(tenderId)` |

**Layer 11 completed: 7/7 issues fixed (100%).**

## Layer 12 — Completed items

| ID | Resolution |
|----|------------|
| L12-1 | `files.py` routes use `Depends(get_db)` (was broken bare `db` param) |
| L12-2 | `/documents/download/*` and `/folders/list` registered before `/{document_id}` |
| L12-3 | `Document` model imported for folder listing query |
| L12-4 | `FileUploader` keeps real `File` references (no empty `new File([])` uploads) |
| L12-5 | `use-file-upload` uses authenticated direct upload + signed-URL fallback |
| L12-6 | OCR router: `require_tenant_member` + RBAC deps; language via query or JSON body |
| L12-7 | `documents-api.ts` unwraps `{ document }` envelopes in hooks |

**Layer 12 completed: 7/7 issues fixed (100%).**

## Layer 13 — Completed items

| ID | Resolution |
|----|------------|
| L13-1 | Billing routes require tenant + `parse_tenant_uuid`; AI usage from `usage_logs` |
| L13-2 | Added `/billing/quota`, `/usage/summary`, subscription change/cancel/reactivate |
| L13-3 | `fe_responses.py` maps API plans/subscription/quota to dashboard JSON shapes |
| L13-4 | `use-billing.ts` calls real endpoints (no mock delays); `initialize()` on billing page |
| L13-5 | `use-usage.ts` uses `/billing/quota` and `/usage/summary` |
| L13-6 | Plan id bridge (`plan_pro` ↔ `professional`); `annual` ↔ `yearly` cycle |
| L13-7 | Stubs for invoices/payment-methods until Stripe integration |

**Layer 13 completed: 7/7 issues fixed (100%).**

## Layer 14 — Completed items

| ID | Resolution |
|----|------------|
| L14-1 | FE `/api/v1/email/triggers/*` aligned via `email_triggers.py` compat router |
| L14-2 | `TriggerRequest` accepts flat JSON bodies from dashboard hooks |
| L14-3 | Email send/trigger paths persist to `email_logs` (removed in-memory `MOCK_LOGS`) |
| L14-4 | `/emails/logs` and `/emails/stats` query `DbEmailLog` by tenant |
| L14-5 | Notifications list unwraps `{ success, data }` + snake_case → camelCase mapper |
| L14-6 | `DELETE /api/v1/notifications/{id}` soft-deletes; list excludes `deleted_at` rows |
| L14-7 | `use-notifications` / `useEmailTriggers` use authenticated `api-client` (no mocks) |

**Layer 14 completed: 7/7 issues fixed (100%).**

## Layer 15 — Completed items

| ID | Resolution |
|----|------------|
| L15-1 | Step 1 returns JWT with `tenant_id` + `membership_role=owner` via `OnboardingSessionTokens` |
| L15-2 | Step 5 re-issues session tokens when onboarding completes |
| L15-3 | Empty `/onboarding/status` includes valid `created_at` / `updated_at` |
| L15-4 | Step 4 accepts `plan_pro` / `annual` aliases (onboarding-specific plan map keeps `free`) |
| L15-5 | `onboarding-api.ts` maps server state; `applyOnboardingSession` updates local storage |
| L15-6 | Step hooks sync from `onboarding_state` on every step (overrides stale persist) |
| L15-7 | Step 4 loads plans from `GET /onboarding/plans` instead of hardcoded FE list |

**Layer 15 completed: 7/7 issues fixed (100%).**

## Layer 16 — Completed items

| ID | Resolution |
|----|------------|
| L16-1 | `export.py` imports `get_current_user`; download route registered after static paths |
| L16-2 | FE `risk_analysis` maps to `/export/risk-analysis/*` + compat `/export/risk_analysis/*` |
| L16-3 | `POST /export/report/{tender_id}` builds analysis payload from DB for PDF/DOCX/JSON/CSV |
| L16-4 | Export jobs return `{ success, data }`; `export-api.ts` parses envelopes |
| L16-5 | Analysis export uses `exportTenderReport` + download (no client-side mock delay) |
| L16-6 | Exports require tenant context (`_tenant_org_id`, no `default` org fallback) |
| L16-7 | Audit log export limited to `csv`/`json`; history rows map to `ExportJob` shape |

**Layer 16 completed: 7/7 issues fixed (100%).**

## Layer 17 — Completed items

| ID | Resolution |
|----|------------|
| L17-1 | Removed hardcoded `MOCK_START_TIME`; real uptime via `set_app_start_time()` in lifespan |
| L17-2 | Tenant metrics require membership; `_tenant_uuid` guard (no cross-tenant null queries) |
| L17-3 | `build_tenant_metrics_summary` computes queue failure + processing success from DB |
| L17-4 | `observability_metrics.py` centralizes summary, failure rate, detailed health |
| L17-5 | `use-observability.ts` + `observability-api.ts`; usage page shows ops summary strip |
| L17-6 | Health dedup: `/observability/health` documents canonical `GET /health`; detailed health uses DB probe |
| L17-7 | `use-analytics` export csv/json only; exposes `isError`; realtime metrics null-safe |

**Layer 17 completed: 7/7 issues fixed (100%).**

## Layer 18 — Completed items

| ID | Resolution |
|----|------------|
| L18-1 | SSO config persisted on `tenants.settings['sso']` via `tenant_store.py` (removed in-memory `SSOService._configs`) |
| L18-2 | Configure/disable use `RequireOrgUpdate`; read config uses `RequireSettingsRead` (no legacy admin string checks) |
| L18-3 | `POST /api/v1/sso/session` exchanges IdP token → JWT via `exchange_sso_session` (mirrors Clerk session flow) |
| L18-4 | Public `GET /sso/public/config` and `/sso/public/login-url`; paths exempt in `tenant_paths.py` |
| L18-5 | `sso-api.ts` + `use-sso.ts`; sign-in supports `?org=<slug>`; profile shows SSO status |
| L18-6 | `SSOHandler` dev email tokens + `GROUP_TO_MEMBERSHIP` → membership role and permissions |
| L18-7 | Routes gated by `FEATURE_SSO`; tests `test_layer18_sso.py` + `sso-api.test.ts` |

**Layer 18 completed: 7/7 issues fixed (100%).**

## Layer 19 — Completed items

| ID | Resolution |
|----|------------|
| L19-1 | Paginated notifications/analysis use `create_paginated_response` with `meta` (not root `total`/`page`) |
| L19-2 | Billing subscription, quota, usage summary wrapped in `create_response`; plans keep `plans` alias |
| L19-3 | `HTTPException` handler returns `{ success: false, error: { code, message, details } }` |
| L19-4 | `parseApiErrorMessage` / `parseApiErrorCode` handle nested `error` and FastAPI `detail` arrays |
| L19-5 | `parsePaginated` lifts legacy root pagination fields for backward compatibility |
| L19-6 | `billing-api.ts` parsers + `use-billing` use envelope-aware unwrap |
| L19-7 | Tests `test_layer19_api_consistency.py` + extended `api-envelope.test.ts` |

**Layer 19 completed: 7/7 issues fixed (100%).**

## Layer 20 — Completed items

| ID | Resolution |
|----|------------|
| L20-1 | `api-config.ts` + `api-fetch.ts` centralize base URL, auth headers, and timeouts |
| L20-2 | Analysis store removed relative `fetch('/api/v1/...')`; uses `analysis-api.ts` + `api` client |
| L20-3 | `use-analysis` and store share `fetchTenderAnalysis` / `patchTenderAnalysisField` |
| L20-4 | File upload + export download use `authenticatedFetch` with `UPLOAD_API_TIMEOUT_MS` |
| L20-5 | Auth/SSO/onboarding raw fetches use `apiUrl()` / `resolveApiUrl()` (no duplicated localhost) |
| L20-6 | `use-api` exposes `getQueryErrorMessage`, `errorMessage`, and `retry: 1` on tender queries |
| L20-7 | Tests `test_layer20_fe_fetching.py` + `api-fetch.test.ts` |

**Layer 20 completed: 7/7 issues fixed (100%).**
