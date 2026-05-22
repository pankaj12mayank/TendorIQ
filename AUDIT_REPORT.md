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
| L10–L35 | See below | 0 | Not started |

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

## Layers 16–35

Export, observability, SSO, API consistency, FE fetching, routes, UX, admin modules, shared package, DB, security, tests, tooling, email system, audit logs, storage, type drift — see [docs/AUDIT_STATUS.md](docs/AUDIT_STATUS.md).

---

# Master fix plan (phased)

## Phase 0 — Unblock E2E (next: L2–L8, L11, L16, L17)

JWT `tenant_id`, `X-Tenant-ID`, Clerk middleware conditional, tenders/analysis/billing/email path alignment.

## Phase 1 — RBAC enforcement + real admin metrics

## Phase 2 — Docs/codegen/hardening

---

*Last updated: Layer 15 completed 7/7 (100%).*
