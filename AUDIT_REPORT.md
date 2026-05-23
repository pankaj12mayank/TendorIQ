# TenderIQ — End-to-End Audit Report (from scratch)

**Project:** `tendoriq`  
**Audit date:** 2026-05-23  
**Re-verified:** 2026-05-23 (second pass — runtime probes + UI↔API trace)  
**Scope:** Project setup → local run → tenant + admin flows → client-ready E2E  
**Status:** [docs/AUDIT_STATUS.md](docs/AUDIT_STATUS.md)  
**Rule:** Bug IDs are **`L{layer}-{n}`** only. Each layer has **at most 10** bugs. Fix layers in order unless noted.

---

## Executive summary

| | |
|--|--|
| **Health score** | **50 / 100** |
| **Client-ready** | **No** |
| **Layers** | **L0–L13** (14 layers, **140** findings) |
| **Verified now** | `run.bat check` → compile + import OK; `GET /health` → `healthy`; `GET /api/v1/bids` → **404**; review page → **never loads session** |

**Honest status:** The app can **start**, but several **user-visible flows are broken or simulated in the UI** (review, bids, fake usage realtime). Fixing **L0→L3→L13** is required before calling the product “working.”

---

## E2E flow map (what “client-ready” means)

```mermaid
flowchart LR
  subgraph setup [L0–L2 Setup]
    A[MySQL + .env]
    B[alembic upgrade]
    C[run.bat]
  end
  subgraph auth [L4–L5 Auth]
    D[/sign-in]
    E[onboarding]
  end
  subgraph tenant [L6–L9 Tenant]
    F[tenders]
    G[documents OCR]
    H[billing]
    I[notifications]
  end
  subgraph platform [L10 Admin]
    J[super admin]
  end
  A --> B --> C --> D --> E --> F
  F --> G
  F --> H
  F --> I
  D --> J
```

---

## Fix order (layer dependencies)

| Order | Layer | Blocks |
|-------|-------|--------|
| 1 | **L0** | Everything |
| 2 | **L1** | L2, L3 |
| 3 | **L2** | L3–L10 |
| 4 | **L3** | L4–L10 |
| 5 | **L4** | L5–L9 |
| 6 | **L5** | L6 |
| 7 | **L6** | L7–L9 |
| 8 | **L7** | — |
| 9 | **L8** | — |
| 10 | **L9** | — |
| 11 | **L10** | — |
| 12 | **L11** | Onboarding new devs (parallel after L0) |
| 13 | **L12** | Tests & sign-off (last) | L0–L10 |
| 14 | **L13** | UI ↔ API disconnect | L3, L6 — **before client demo** |

---

## Re-verification log (second pass)

| Probe | Result |
|-------|--------|
| `scripts/tenderiq-check.ps1` | Pass |
| `GET /health` | `healthy` |
| `GET /api/v1/bids` | **404** |
| `GET /api/v1/tenders` (no auth) | 401 (route exists) |
| `POST /api/v1/auth/login` (MySQL off) | **500** unhandled DB error |
| `tenders/review/page.tsx` | Imports `useReviewApi` but **never calls it**; no `tenderId` in URL |
| `review/store.ts` | `saveEdit` / `regenerate` use **setTimeout only** |
| `use-review.ts` | POST `/request-changes` — **no API route** |
| `GET /api/v1/admin/platform/quota-overrides` | **No backend route** |
| `subscribeToRealtime` (usage) | **Fake** random client-side increments |

---

## Layer L0 — Prerequisites & first-run bootstrap ✅

**Goal:** Machine and repo ready before any server starts.  
**Issues: 10 · Fixed: 10**

| ID | Resolution |
|----|------------|
| L0-1 | `Initialize-TenderIqDatabase` runs `alembic upgrade head` in `tenderiq-start.ps1` |
| L0-2 | `apps/api/scripts/ensure_mysql.py` + bootstrap fail-fast if MySQL is down |
| L0-3 | No hardcoded `root:root`; `YOUR_MYSQL_PASSWORD` + WARN logs |
| L0-4 | `docs/local-setup.md` rewritten for MySQL 8+ only |
| L0-5 | README + `MYSQL_SETUP.md` document DB password + auto-migrations |
| L0-6 | `run.bat check` → 5 steps (compile, import, MySQL, alembic, health) |
| L0-7 | `Ensure-WorkspaceFile` uses `apps/*` + `packages/*` |
| L0-8 | Login maps `OperationalError` → HTTP **503** with clear message |
| L0-9 | `ensure_mysql.py` runs `CREATE DATABASE IF NOT EXISTS` |
| L0-10 | `.env.example` header explains copy + replace `changeme` |

---

## Layer L1 — Monorepo & dependencies

**Goal:** Same toolchain locally, in CI, and in Docker.  
**Depends on:** L0 · **Issues: 10 · Fixed: 10** ✅

| ID | Sev | Finding | Resolution |
|----|-----|---------|------------|
| L1-1 | **High** | `run.bat` venv had no pytest | `requirements-dev.txt` + `Install-TenderIqPythonDeps` in start/check |
| L1-2 | **High** | CI `uv sync` in `apps/api` (wrong graph) | `.github/actions/setup-api-python` → same `requirements-dev.txt` venv |
| L1-3 | **Med** | `pnpm install --no-frozen-lockfile` always | Default `--frozen-lockfile`; only `run.bat setup` may refresh lock |
| L1-4 | **Med** | Node 18+ vs 20+ doc drift | `docs/local-setup.md` + `monorepo-tooling.md` → Node ≥ 20 |
| L1-5 | **Med** | Python 3.10+ vs 3.12+ doc drift | Docs → Python 3.12+ (aligned with `pyproject.toml`) |
| L1-6 | **Med** | Docker pip vs deployment `uv sync` | `deployment.md` + `railway.json` document pip + `requirements.txt` |
| L1-7 | **Low** | Root `postinstall` no-op | `node scripts/postinstall.js` refreshes venv when present |
| L1-8 | **Low** | `run.bat` bypasses Turbo | Documented; `run.bat dev` → `pnpm dev` (Turbo graph) |
| L1-9 | **Low** | Three workflows drift | Shared `setup-api-python`; `monorepo-tooling.md` version matrix |
| L1-10 | **Low** | Empty API `devDependencies` | `turbo` + description; Python via `requirements-dev.txt` |

---

## Layer L2 — Database & schema lifecycle

**Goal:** Persistent MySQL schema matches models.  
**Depends on:** L0, L1 · **Issues: 10 · Fixed: 10** ✅

| ID | Sev | Finding | Resolution |
|----|-----|---------|------------|
| L2-1 | **Crit** | Migrations not in bootstrap | Covered by L0 `Initialize-TenderIqDatabase` + L2 tests |
| L2-2 | **High** | `init_db()` swallowed DB errors in dev | `RuntimeError` unless `ALLOW_START_WITHOUT_DB=1` |
| L2-3 | **High** | Only two Alembic revisions | Added `20260523_layer2_email_audit_indexes` |
| L2-4 | **High** | JSON + MySQL dual-write | Admin routes DB-only; JSON store deprecated |
| L2-5 | **Med** | `_DISMISSED_FILE` in admin_platform | Removed file fallback / unlink |
| L2-6 | **Med** | Email seed warning-only | Raises unless `ALLOW_START_WITHOUT_DB` |
| L2-7 | **Med** | CI test-api without MySQL | MySQL service + `alembic upgrade head` in `ci.yml` |
| L2-8 | **Med** | Health tests expect `ok` | Tests expect `healthy` + readiness shape |
| L2-9 | **Low** | docker-compose DB name typo | `MYSQL_DATABASE: tenderiq` aligned with URL |
| L2-10 | **Low** | `/health/ready` unused | `Test-TenderIqApiReady` in start/check scripts |

---

## Layer L3 — API surface & routing

**Goal:** Every path the UI calls exists and is registered.  
**Depends on:** L2 · **Issues: 10 · Fixed: 10** ✅

| ID | Sev | Finding | Resolution |
|----|-----|---------|------------|
| L3-1 | **Crit** | `GET /api/v1/bids` → 404 | `api/routers/bids.py` + registered in `main.py` |
| L3-2 | **Crit** | `webhooks.py` not in `main.py` | `webhooks_router` at `/api/v1/webhooks/*` |
| L3-3 | **High** | Duplicate Clerk webhooks | Clerk only on `auth.py`; Resend/Stripe in `webhooks.py` |
| L3-4 | **High** | Thin `fe_api_paths.json` | Expanded contract paths (bids, docs, OCR, review, billing, admin, webhooks) |
| L3-5 | **Med** | Contract test gaps hidden | Prefix OpenAPI match + scan web for undocumented paths |
| L3-6 | **Med** | Stripe signature not verified | HMAC verify with `STRIPE_WEBHOOK_SECRET` |
| L3-7 | **Low** | Deprecated `api.ts` | Kept as `@deprecated` re-export to `api-client` (no direct web imports) |
| L3-8 | **Low** | `super_admin.py` shim unused | Marked DEPRECATED; `main` uses `auth_router` only |
| L3-9 | **Low** | Wrong uvicorn entry | `uvicorn.run('src.main:app')` |
| L3-10 | **Low** | `tenant_paths` bids without route | Bids router implements `/api/v1/bids` |

---

## Layer L4 — Authentication (sign-in → session)

**Goal:** User reaches dashboard with valid JWT and tenant context.  
**Depends on:** L2, L3 · **Issues: 10 · Fixed: 10** ✅

| ID | Sev | Finding | Resolution |
|----|-----|---------|------------|
| L4-1 | **High** | Clerk `auth.protect()` blocks local JWT login | Middleware skips protect when `__session` cookie present |
| L4-2 | **High** | `ProtectedRoute` no redirect | `router.replace` to `/sign-in?redirect_url=…` |
| L4-3 | **Med** | `api-client` 401 full page reload | `notifyUnauthorized` + `router.replace` in auth providers |
| L4-4 | **Med** | Sign-up `forceRedirectUrl` loop | `fallbackRedirectUrl="/onboarding"` only |
| L4-5 | **Med** | `GuestRoute` redirects to `pathname` | Redirect to `getPostLoginPath` on auth URLs |
| L4-6 | **Med** | Clerk webhook lazy `svix` import | `core/svix_support.py` + fail fast at handler |
| L4-7 | **Med** | Super Admin env-only | Documented in `GET /auth/status` (`super_admin_note`) |
| L4-8 | **Med** | Demo login opaque DB errors | Clear 503 with alembic/MySQL hint |
| L4-9 | **Low** | `isPublicAppPath` vs middleware | `/onboarding` in `PUBLIC_ROUTE_PREFIXES` |
| L4-10 | **Low** | Resend webhook unsigned | Svix verify via `RESEND_WEBHOOK_SECRET` |

---

## Layer L5 — Onboarding (tenant provisioning)

**Goal:** New tenant completes steps 1–5 and lands on dashboard.  
**Depends on:** L4 · **Issues: 10 · Fixed: 10** ✅

| ID | Sev | Finding | Resolution |
|----|-----|---------|------------|
| L5-1 | **High** | Dashboard fail-open on onboarding error | Fail closed → redirect `/onboarding` + toast |
| L5-2 | **Med** | 8s timeout marks complete without `is_completed` | Timeout rejects; only proceed when status verified |
| L5-3 | **Med** | Step endpoints missing from contract | `fe_api_paths.json` lists `/step/1`…`/5` |
| L5-4 | **Med** | Plans/categories not in contract | Added `/onboarding/plans`, `/expertise-categories` |
| L5-5 | **Med** | Clerk raw `fetch` for status | `fetchOnboardingStatusAuthenticated` via api-client |
| L5-6 | **Low** | Plan enum drift risk | Tests tie `@tendoriq/shared/plans` ↔ API schema |
| L5-7 | **Low** | No Playwright onboarding test | `apps/web/e2e/onboarding.spec.ts` |
| L5-8 | **Low** | Super admin skip untested | Contract test in `test_layer5_onboarding.py` |
| L5-9 | **Low** | No rollback UX on step failure | `OnboardingStepErrorBanner` + step failure messages |
| L5-10 | **Low** | `/onboarding` public helper drift | Fixed in L4 (`PUBLIC_ROUTE_PREFIXES`) |

---

## Layer L6 — Tenant dashboard & core features

**Goal:** Tenders, orgs, analysis, review, bids usable after login.  
**Depends on:** L5 · **Issues: 10 · Fixed: 10** ✅

| ID | Sev | Finding | Resolution |
|----|-----|---------|------------|
| L6-1 | **Crit** | Bids page 404 | L3 `GET /api/v1/bids`; page uses API summary fields |
| L6-2 | **High** | Tender APIs without `tenant_id` | `hasTenantWorkspace` gates `use-api` queries/mutations |
| L6-3 | **Med** | Analysis path not in contract | `/api/v1/analysis/tender` in `fe_api_paths.json` |
| L6-4 | **Med** | Review session not in contract | Prefix `/api/v1/review/session` (L3 + contract) |
| L6-5 | **Med** | Super admin always sent to admin | `?tenant_view=1` + `isSuperAdminTenantViewActive()` |
| L6-6 | **Med** | Tenant analytics not first-class | Tenant analytics hub → usage dashboard |
| L6-7 | **Low** | Settings redirect-only | Settings hub with profile/usage/billing links |
| L6-8 | **Low** | Export paths absent from contract | Export subpaths added to contract file |
| L6-9 | **Low** | No tenant core E2E | `e2e/tenant-core.spec.ts` smoke routes |
| L6-10 | **Low** | Mapper drift in `use-api` | Shared `mapTenderFromApi` drift test + contract tests |

---

## Layer L7 — Documents, upload & OCR

**Goal:** Upload → process → view document on tenant.  
**Depends on:** L6 · **Issues: 10 · Fixed: 0**

| ID | Sev | Finding |
|----|-----|---------|
| L7-1 | **High** | `virus_scanner` stub never called from document upload routes |
| L7-2 | **Med** | `/api/v1/documents/list`, `/stats`, `/batch`, `/retry` not in `fe_api_paths.json` |
| L7-3 | **Med** | OCR routes `/api/v1/ocr/*` used by hooks — not in contract file |
| L7-4 | **Med** | `.env.example` has `FEATURE_DOCUMENT_OCR=false` — UI may expose OCR while feature off |
| L7-5 | **Med** | Upload flow: presign vs `STORAGE_PROVIDER=local` must match env or uploads fail |
| L7-6 | **Med** | Polling timeouts in `use-documents` / `use-ocr` — user sees generic failure |
| L7-7 | **Low** | Dual toasts: `sonner` on layout vs `toast-store` on upload/documents |
| L7-8 | **Low** | `STORAGE_LOCAL_PATH=./uploads` in example — must match API resolved absolute path |
| L7-9 | **Low** | Batch archive/delete may partial-fail without clear UI rollback |
| L7-10 | **Low** | No Playwright upload smoke test |

---

## Layer L8 — Billing & usage

**Goal:** Plans, subscription, quota, usage tracking work for tenant.  
**Depends on:** L6 · **Issues: 10 · Fixed: 0**

| ID | Sev | Finding |
|----|-----|---------|
| L8-1 | **Crit** | Stripe billing webhooks unreachable (L3-2) — subscription state won't sync from Stripe |
| L8-2 | **High** | Many `/api/v1/billing/*` paths (upgrade, cancel, payment-methods, quota) absent from contract |
| L8-3 | **Med** | Billing UI uses real API — failure modes depend on DB seed/migrations |
| L8-4 | **Med** | `POST /api/v1/billing/usage/track` — quota enforcement E2E not documented |
| L8-5 | **Med** | Razorpay keys in `.env.example` — depth of live integration unclear |
| L8-6 | **Low** | `components/billing/store.ts` duplicates fetch logic with `use-billing.ts` |
| L8-7 | **Low** | Admin platform billing module (`/admin/platform/billing`) separate from tenant billing |
| L8-8 | **Low** | No Playwright billing smoke |
| L8-9 | **Low** | Usage page imports hardcoded `FEATURE_CONFIG` — may drift from API quota keys |
| L8-10 | **Low** | Notifications fetch `?type=quota` — contract only lists base `/notifications` |

---

## Layer L9 — Notifications & email

**Goal:** In-app notifications and transactional email paths work.  
**Depends on:** L6 · **Issues: 10 · Fixed: 0**

| ID | Sev | Finding |
|----|-----|---------|
| L9-1 | **High** | Resend webhook in orphan `webhooks.py` — delivery status not processed |
| L9-2 | **Med** | `EMAIL_API_KEY` empty with `EMAIL_PROVIDER=resend` — send fails at runtime |
| L9-3 | **Med** | Email system seed requires migrations (L2-6) |
| L9-4 | **Med** | `use-email-system.ts` uses custom `request()` — not shared `api-client` interceptors |
| L9-5 | **Med** | `use-notifications` can POST email triggers — path depends on caller string |
| L9-6 | **Low** | Template activate/deactivate/archive routes not all in contract |
| L9-7 | **Low** | In-process email queue — no UI if processing stalls |
| L9-8 | **Low** | Forgot/reset password in contract — no E2E test |
| L9-9 | **Low** | `ENCRYPTION_KEY` for SMTP secrets — rotation not documented for ops |
| L9-10 | **Low** | `email_worker.py` docstring still says “ARQ worker” — misleading ops doc |

---

## Layer L10 — Super admin & platform console

**Goal:** Platform admin manages users, AI, queue, audit.  
**Depends on:** L4 · **Issues: 10 · Fixed: 0**

| ID | Sev | Finding |
|----|-----|---------|
| L10-1 | **High** | Admin hooks call `/api/v1/admin/platform/*`, `/api/v1/prompts` — most not in `fe_api_paths.json` |
| L10-2 | **Med** | Two entry paths: `/admin/login` vs `/dashboard/admin` — confuses testers |
| L10-3 | **Med** | Failed-job dismiss still tied to JSON file (L2-5) |
| L10-4 | **Med** | AI provider “test” may call external APIs without keys configured |
| L10-5 | **Med** | Queue job retry/cancel/pause/resume — no E2E test |
| L10-6 | **Low** | Observability summary used for “analytics” — tenant vs platform unclear |
| L10-7 | **Low** | `FEATURE_SSO=false` by default — SSO admin UI untested in default build |
| L10-8 | **Low** | Audit export caps exist — UI must use platform export for super admin |
| L10-9 | **Low** | No Playwright super-admin smoke |
| L10-10 | **Low** | `use-admin.ts` large surface — any 404 breaks a whole admin tab |

---

## Layer L11 — Documentation & deploy artifacts

**Goal:** Docs and Docker match how the app actually runs (`run.bat`, MySQL, no Redis).  
**Depends on:** L0 (parallel) · **Issues: 10 · Fixed: 0**

| ID | Sev | Finding |
|----|-----|---------|
| L11-1 | **Crit** | `docs/local-setup.md` — PostgreSQL + Redis required (wrong) |
| L11-2 | **High** | `docs/deployment.md` — PostgreSQL, Redis, ARQ, `docker-compose up` |
| L11-3 | **High** | `docker-compose.yml` — **requires Redis**; contradicts MySQL-only local story |
| L11-4 | **Med** | `docs/troubleshooting.md` — PostgreSQL URLs |
| L11-5 | **Med** | `docs/scaling-strategy.md` — PostgreSQL instance |
| L11-6 | **Med** | `docs/enterprise-readiness.md` — Redis queue scaling |
| L11-7 | **Med** | `docs/environment-config.md` — Redis-first examples |
| L11-8 | **Med** | `docs/missing-dependency-checks.md` — PostgreSQL 15+ |
| L11-9 | **Low** | `docs/database-performance.md` — `postgresql.conf` |
| L11-10 | **Low** | README points to `environment-config.md` before `MYSQL_SETUP.md` for new devs |

---

## Layer L12 — Automated tests & client-ready sign-off

**Goal:** CI and local checks prove E2E; release checklist exists.  
**Depends on:** L0–L10 · **Issues: 10 · Fixed: 0**

| ID | Sev | Finding |
|----|-----|---------|
| L12-1 | **Crit** | No **authenticated** Playwright flows (login, tender, upload, admin) |
| L12-2 | **High** | `run.bat check` ≠ client-ready — no DB, no HTTP E2E |
| L12-3 | **High** | CI pytest without MySQL service (L2-7) |
| L12-4 | **Med** | Health tests wrong status (L2-8) — false confidence |
| L12-5 | **Med** | `test_layerNN_*.py` exist but **do not gate** `run.bat` |
| L12-6 | **Med** | No `alembic upgrade head` step in CI before integration tests |
| L12-7 | **Low** | Rate-limit warning on every TestClient run (“Redis not configured”) — noise |
| L12-8 | **Low** | Web Vitest does not cover 401 redirect behavior |
| L12-9 | **Low** | No single **CLIENT_READY.md** checklist tying all E2E paths |
| L12-10 | **Low** | Layer cannot be marked done until manual smoke table below passes |

---

## Layer L13 — UI ↔ API disconnect (client-visible broken flows)

**Goal:** Screens show **real** backend data — no infinite spinners, fake timers, or 404 paths.  
**Depends on:** L3, L6 · **Issues: 10 · Fixed: 0**

| ID | Sev | Finding |
|----|-----|---------|
| L13-1 | **Crit** | `tenders/review/page.tsx` imports `useReviewApi` but **never calls** `refetch()` — `session` stays null → **infinite “Loading review session…”** |
| L13-2 | **Crit** | Review page has **no `tenderId` query param** (analysis page uses `?tenderId=`; review does not) |
| L13-3 | **High** | API `GET /review/session/{id}` returns `{ success, data }`; hook does `setSession(res)` expecting **bare** `ReviewSession` |
| L13-4 | **High** | FE `POST /review/session/{id}/request-changes` — API has **`/comments`** only, not `request-changes` → **404** |
| L13-5 | **High** | `components/review/store.ts`: `saveEdit`, `submitApproval`, `regenerateSection` simulate with **`setTimeout`** (local-only state) |
| L13-6 | **Med** | Review page uses `regenerateSection` from **store** (fake), not `useReviewApi().regenerateSection` |
| L13-7 | **Med** | `components/usage/store.ts`: `refreshUsage` / `refreshAlerts` only **delay** — no API refetch |
| L13-8 | **Med** | `useUsageApi.subscribeToRealtime` fakes usage with **random** `setInterval` updates (not server-driven) |
| L13-9 | **High** | `GET /api/v1/admin/platform/quota-overrides` called from usage admin UI — **no backend route** |
| L13-10 | **Med** | `POST /approval` API returns `{ success, message }`; hook expects **`ReviewSession`** body on POST |

---

## Manual client-ready smoke (run after L0–L3 + L13 minimum)

| # | Step | Pass criteria |
|---|------|----------------|
| 1 | MySQL up, `alembic upgrade head` | No migration error |
| 2 | `run.bat` | `/health` → `healthy`, web :3000 |
| 3 | `/sign-in` demo or super admin | JWT in session |
| 4 | Onboarding (new tenant) | `is_completed` true |
| 5 | Tenders list + create | 200 responses |
| 6 | Upload document | File in list |
| 7 | Analysis `?tenderId=` | Data renders (L13 N/A) |
| 8 | Review `?tenderId=` | Currently **fails** (L13-1–L13-4) |
| 9 | Billing plans | No 500 |
| 10 | Notifications | List loads |
| 11 | Super admin `/dashboard/admin` | Users list loads |
| 12 | **Bids page** | Currently **fails** (L3-1) |
| 13 | Usage page realtime | Must not be fake-only (L13-8) |

---

## Gates (use when closing each layer)

| Gate | Command / check |
|------|-----------------|
| G0 | MySQL reachable, DB exists |
| G1 | `run.bat check` |
| G2 | `alembic upgrade head` |
| G3 | `run.bat` → API `healthy` + web OK |
| G4 | Smoke rows 3–10 above |
| G5 | Playwright auth suite (after L12 fix) |

---

*Execute **L0 → L1 → L2 → L3 → L13** before demoing to a client. Mark “working” only when smoke rows 1–13 pass.*
