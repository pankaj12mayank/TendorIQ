# TenderIQ — Audit status

**Report:** [AUDIT_REPORT.md](../AUDIT_REPORT.md)  
**Started:** 2026-05-23 (scratch audit, L0+)  
**Prior audits:** Discarded — do not use old L1–L35 / L36–L44 IDs.

---

## Summary

| | |
|--|--|
| Health | 100 / 100 |
| Client-ready | Run `run.bat gates` (G0-G5); manual UI smoke in CLIENT_READY.md |
| Layers | L0–L13 |
| Total bugs | 140 |
| Fixed | 140 (L0–L13 complete) |
| Re-verified | 2026-05-23 (second pass) |

---

## Execution order

| Step | Layer | Title | Fixed | Status |
|------|-------|-------|-------|--------|
| 1 | L0 | Prerequisites & bootstrap | 10/10 | **Done** |
| 2 | L1 | Monorepo & dependencies | 10/10 | **Done** |
| 3 | L2 | Database & schema | 10/10 | **Done** |
| 4 | L3 | API routes & contract | 10/10 | **Done** |
| 5 | L4 | Authentication | 10/10 | **Done** |
| 6 | L5 | Onboarding | 10/10 | **Done** |
| 7 | L6 | Tenant dashboard | 10/10 | **Done** |
| 8 | L7 | Documents & OCR | 10/10 | **Done** |
| 9 | L8 | Billing & usage | 10/10 | **Done** |
| 10 | L9 | Notifications & email | 10/10 | **Done** |
| 11 | L10 | Super admin | 10/10 | **Done** |
| 12 | L11 | Docs & deploy | 10/10 | **Done** |
| 13 | L12 | Tests & client sign-off | 10/10 | **Done** |
| 14 | L13 | UI ↔ API disconnect | 10/10 | **Done** |

**Critical path for “working”:** L0 → L1 → L2 → L3 → **L13** → L4 → L5 → L6…

**Rule:** Fix layers in order. Mark an ID **Fixed** only after you verify the smoke step that covers it.

---

## Gates

| Gate | Command | Status |
|------|---------|--------|
| G0 MySQL + DB | `run.bat gates` (step 1) | Requires local MySQL on localhost:3306 |
| G1 `run.bat check` | `run.bat gates` (step 2) | Layer tests + OpenAPI contract |
| G2 `alembic upgrade head` | `run.bat gates` (step 3) | Requires G0 |
| G3 Stack | `run.bat gates` (step 4) | API :8000 + web :3000 |
| G4 API smoke | `run.bat gates` (step 5) | `apps/api/scripts/smoke_gate.py` |
| G5 Playwright | `run.bat gates` (step 6) | chromium + chromium-authenticated |

Run all: **`run.bat gates`** from repo root (see [CLIENT_READY.md](CLIENT_READY.md)).

---

## L0 — Prerequisites (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L0-1 | Critical | **Fixed** | `alembic upgrade head` in `tenderiq-start.ps1` |
| L0-2 | Critical | **Fixed** | `ensure_mysql.py` + fail-fast if MySQL down |
| L0-3 | High | **Fixed** | No `root:root`; placeholder warnings |
| L0-4 | High | **Fixed** | `docs/local-setup.md` MySQL-only |
| L0-5 | Medium | **Fixed** | README + MYSQL_SETUP prerequisites |
| L0-6 | Medium | **Fixed** | `run.bat check` → MySQL + alembic |
| L0-7 | Medium | **Fixed** | `pnpm-workspace.yaml` → `apps/*` |
| L0-8 | Low | **Fixed** | Login `OperationalError` → 503 |
| L0-9 | Low | **Fixed** | `ensure_mysql.py` creates database |
| L0-10 | Low | **Fixed** | `.env.example` copy instructions |

## L1 — Dependencies (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L1-1 | High | **Fixed** | `requirements-dev.txt` installed into `apps/api/venv` |
| L1-2 | High | **Fixed** | CI action `setup-api-python` mirrors local venv |
| L1-3 | Medium | **Fixed** | Frozen lockfile by default in `tenderiq-start.ps1` |
| L1-4 | Medium | **Fixed** | Docs: Node ≥ 20 |
| L1-5 | Medium | **Fixed** | Docs: Python 3.12+ |
| L1-6 | Medium | **Fixed** | `deployment.md` / Railway align with Dockerfile pip |
| L1-7 | Low | **Fixed** | `postinstall.js` wires optional venv refresh |
| L1-8 | Low | **Fixed** | `run.bat dev` + monorepo doc |
| L1-9 | Low | **Fixed** | Shared CI action + tooling doc |
| L1-10 | Low | **Fixed** | `@tendoriq/api` package metadata + turbo devDep |

## L2 — Database (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L2-1 | Critical | **Fixed** | Alembic in bootstrap (L0 + verified) |
| L2-2 | High | **Fixed** | `init_db` fail-fast; opt-out env for unit tests |
| L2-3 | High | **Fixed** | Third migration: email/audit indexes |
| L2-4 | High | **Fixed** | Admin platform MySQL-only |
| L2-5 | Medium | **Fixed** | No `_DISMISSED_FILE` in routes |
| L2-6 | Medium | **Fixed** | Email seed raises without DB/migrations |
| L2-7 | Medium | **Fixed** | CI MySQL + migrations |
| L2-8 | Medium | **Fixed** | Health tests use `healthy` |
| L2-9 | Low | **Fixed** | docker-compose `tenderiq` DB name |
| L2-10 | Low | **Fixed** | Startup/check use `/health/ready` |

## L3 — API routes (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L3-1 | Critical | **Fixed** | `GET /api/v1/bids` router |
| L3-2 | Critical | **Fixed** | Webhooks registered in `main.py` |
| L3-3 | High | **Fixed** | Single Clerk endpoint on auth router |
| L3-4 | High | **Fixed** | Expanded `fe_api_paths.json` |
| L3-5 | Medium | **Fixed** | OpenAPI prefix match + web path scan |
| L3-6 | Medium | **Fixed** | Stripe HMAC verification |
| L3-7 | Low | **Fixed** | Deprecated `api.ts` shim documented |
| L3-8 | Low | **Fixed** | `super_admin.py` marked deprecated |
| L3-9 | Low | **Fixed** | `src.main:app` entrypoint |
| L3-10 | Low | **Fixed** | Bids route matches `tenant_paths` |

## L4 — Auth (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L4-1 | High | **Fixed** | `__session` bypass in Clerk middleware |
| L4-2 | High | **Fixed** | ProtectedRoute → sign-in redirect |
| L4-3 | Medium | **Fixed** | auth-unauthorized handler (no full reload) |
| L4-4 | Medium | **Fixed** | Sign-up fallbackRedirectUrl only |
| L4-5 | Medium | **Fixed** | GuestRoute post-login redirect |
| L4-6 | Medium | **Fixed** | `svix_support` module |
| L4-7 | Medium | **Fixed** | `/auth/status` super_admin_note |
| L4-8 | Medium | **Fixed** | Demo login 503 with migration hint |
| L4-9 | Low | **Fixed** | onboarding in public routes helper |
| L4-10 | Low | **Fixed** | Resend Svix signature verify |

## L5 — Onboarding (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L5-1 | High | **Fixed** | Dashboard fail-closed |
| L5-2 | Medium | **Fixed** | Verified status only (no blind timeout) |
| L5-3 | Medium | **Fixed** | Contract paths for steps 1–5 |
| L5-4 | Medium | **Fixed** | Plans + expertise in contract |
| L5-5 | Medium | **Fixed** | Shared onboarding-api helper |
| L5-6 | Low | **Fixed** | Plan alignment tests |
| L5-7 | Low | **Fixed** | Playwright onboarding spec |
| L5-8 | Low | **Fixed** | Super admin skip tested |
| L5-9 | Low | **Fixed** | Step error banner + recovery |
| L5-10 | Low | **Fixed** | L4 public routes (onboarding) |

## L6 — Tenant dashboard (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L6-1 | Critical | **Fixed** | Bids API + page |
| L6-2 | High | **Fixed** | Tenant workspace guard on tenders |
| L6-3 | Medium | **Fixed** | Analysis contract path |
| L6-4 | Medium | **Fixed** | Review session contract prefix |
| L6-5 | Medium | **Fixed** | Super admin `tenant_view` override |
| L6-6 | Medium | **Fixed** | Tenant analytics hub |
| L6-7 | Low | **Fixed** | Settings hub page |
| L6-8 | Low | **Fixed** | Export paths in contract |
| L6-9 | Low | **Fixed** | `tenant-core` Playwright spec |
| L6-10 | Low | **Fixed** | Shared tender mapper drift test |

## L7 — Documents (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L7-1 | High | **Fixed** | `upload_scan.assert_upload_clean` |
| L7-2 | Medium | **Fixed** | Contract paths for documents API |
| L7-3 | Medium | **Fixed** | Contract paths for OCR API |
| L7-4 | Medium | **Fixed** | Feature flag gates (API + web) |
| L7-5 | Medium | **Fixed** | Direct upload first + env docs |
| L7-6 | Medium | **Fixed** | `polling-errors.ts` |
| L7-7 | Low | **Fixed** | Sonner-only toasts |
| L7-8 | Low | **Fixed** | `.env.example` storage notes |
| L7-9 | Low | **Fixed** | Batch partial-failure UX |
| L7-10 | Low | **Fixed** | Playwright upload smoke |

## L8 — Billing (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L8-1 | Critical | **Fixed** | Stripe webhook sync |
| L8-2 | High | **Fixed** | Contract paths |
| L8-3 | Medium | **Fixed** | Billing errors + docs |
| L8-4 | Medium | **Fixed** | Quota track doc |
| L8-5 | Medium | **Fixed** | Razorpay documented |
| L8-6 | Low | **Fixed** | UI-only billing store |
| L8-7 | Low | **Fixed** | Admin module comment |
| L8-8 | Low | **Fixed** | Playwright billing spec |
| L8-9 | Low | **Fixed** | API-driven feature labels |
| L8-10 | Low | **Fixed** | Notifications prefix contract |

## L9 — Notifications (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L9-1 | High | **Fixed** | Resend webhook → `email_logs` |
| L9-2 | Medium | **Fixed** | Startup warning + `.env.example` |
| L9-3 | Medium | **Fixed** | Migration/seed in `EMAIL_SYSTEM.md` |
| L9-4 | Medium | **Fixed** | `use-email-system` uses `api-client` |
| L9-5 | Medium | **Fixed** | `email-trigger-paths.ts` |
| L9-6 | Low | **Fixed** | Contract template/queue paths |
| L9-7 | Low | **Fixed** | Queue stall UI + retry |
| L9-8 | Low | **Fixed** | Playwright password reset spec |
| L9-9 | Low | **Fixed** | `ENCRYPTION_KEY` rotation doc |
| L9-10 | Low | **Fixed** | `email_worker` docstring |

## L10 — Super admin (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L10-1 | High | **Fixed** | Contract paths |
| L10-2 | Medium | **Fixed** | Legacy redirect + doc |
| L10-3 | Medium | **Fixed** | DB dismiss only |
| L10-4 | Medium | **Fixed** | AI test dry-run |
| L10-5 | Medium | **Fixed** | Playwright queue smoke |
| L10-6 | Low | **Fixed** | Platform analytics labels |
| L10-7 | Low | **Fixed** | SSO flags documented |
| L10-8 | Low | **Fixed** | Platform audit export |
| L10-9 | Low | **Fixed** | `super-admin.spec.ts` |
| L10-10 | Low | **Fixed** | Split admin hooks |

## L11 — Docs & deploy (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L11-1 | Critical | **Fixed** | `local-setup.md` MySQL + run.bat |
| L11-2 | High | **Fixed** | `deployment.md` rewrite |
| L11-3 | High | **Fixed** | `docker-compose.yml` optional Redis |
| L11-4 | Medium | **Fixed** | `troubleshooting.md` MySQL |
| L11-5 | Medium | **Fixed** | `scaling-strategy.md` banner |
| L11-6 | Medium | **Fixed** | `enterprise-readiness.md` |
| L11-7 | Medium | **Fixed** | `environment-config.md` |
| L11-8 | Medium | **Fixed** | `missing-dependency-checks.md` |
| L11-9 | Low | **Fixed** | `database-performance.md` |
| L11-10 | Low | **Fixed** | README doc order |

## L12 — Tests & sign-off (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L12-1 | Critical | **Fixed** | Authenticated Playwright + setup |
| L12-2 | High | **Fixed** | `run.bat e2e` + CLIENT_READY |
| L12-3 | High | **Fixed** | CI MySQL service |
| L12-4 | Medium | **Fixed** | Health/ready tests |
| L12-5 | Medium | **Fixed** | Layer bundle in check script |
| L12-6 | Medium | **Fixed** | Alembic in integration CI |
| L12-7 | Low | **Fixed** | Rate limit off in tests |
| L12-8 | Low | **Fixed** | Vitest 401 redirect |
| L12-9 | Low | **Fixed** | CLIENT_READY.md |
| L12-10 | Low | **Fixed** | Manual smoke table in doc |

## L13 — UI ↔ API disconnect (10/10) ✅

| ID | Sev | Status | Resolution |
|----|-----|--------|------------|
| L13-1 | Critical | **Fixed** | Auto refetch on mount |
| L13-2 | Critical | **Fixed** | `?tenderId=` query param |
| L13-3 | High | **Fixed** | `review-api` envelope mapper |
| L13-4 | High | **Fixed** | Approval endpoint for changes |
| L13-5 | High | **Fixed** | Removed fake store mutations |
| L13-6 | Medium | **Fixed** | API regenerate in hook |
| L13-7 | Medium | **Fixed** | Real usage refresh handlers |
| L13-8 | Medium | **Fixed** | Billing poll, not random |
| L13-9 | High | **Fixed** | Quota-overrides API route |
| L13-10 | Medium | **Fixed** | Refetch after approval POST |

---

*Update Fixed counts when closing bugs. Say “L0 fix karo” to implement layer L0 only.*
