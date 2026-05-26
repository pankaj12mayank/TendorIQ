# TenderIQ Lite — Client-ready status (PRD audit)

**Date:** 2026-05-26  
**Scope:** [TENDERIQ_LITE_IMPLEMENTATION_PLAN.md](./TENDERIQ_LITE_IMPLEMENTATION_PLAN.md) (FINAL MINI PRD)

---

## Executive summary

| Area | Code | Your machine (E2E) |
|------|------|-------------------|
| **Overall** | **~98% PRD** | **~90%** after `run.bat` + demo login |
| Blockers fixed this audit | Public site 500 without migrations; Important Clauses UI missing; unit test flake | — |
| You must run once | — | `run.bat` (runs migrations + starts servers) |

**Verdict:** Client-ready for **Lite MVP demo** with **local auth** (`AUTH_PROVIDER=local`). Supabase Postgres / full Supabase Auth E2E remain **optional** PRD deviations documented below.

---

## PRD checklist (exact scope)

| # | PRD requirement | Status | Notes |
|---|-----------------|--------|-------|
| 1 | 9 routes: `/`, sign-in, sign-up, dashboard, upload, analysis, proposal, settings, admin | **Done** | Billing/profile/ai → settings tabs (redirects) |
| 2 | Real upload (no fake progress) | **Done** | `FileUploader` → API |
| 3 | PDF/DOCX 25MB | **Done** | `upload_policy.py` |
| 4 | AI analysis + **important clauses** | **Done** | API + analysis UI tab **Clauses** |
| 5 | Proposal generation | **Done** | `/api/v1/proposals/*` |
| 6 | PDF-only export | **Done** | `LITE_EXPORT_PDF_ONLY=true` |
| 7 | Company profile in PDF | **Done** | Settings → Profile / company |
| 8 | Demo quotas | **Done** | `lite_usage.py`, billing tab |
| 9 | Razorpay | **Done** | Needs test keys in `.env` (optional demo) |
| 10 | Admin: users, pricing, AI, landing, uploads | **Done** | `/dashboard/admin` |
| 11 | Local auth without cloud keys | **Done** | `docs/LOCAL_SETUP.md` |
| 12 | No Redis/ARQ queues | **Done** | `tasks/inline.py` |
| 13 | Deploy docs + Docker | **Done** | `docs/DEPLOY.md` |

---

## Intentional PRD deviations (documented, not blockers)

| PRD | Actual | Why |
|-----|--------|-----|
| Vite frontend | Next.js 15 | Speed; documented in plan §11 |
| Supabase Postgres | SQLite/MySQL local | Phase 1 scope; B4 in tracker |
| Drop `tenants` table | Kept as workspace | Required for billing/quotas |
| Supabase-only auth | Local + optional Supabase/Clerk | Local default for client demo |
| Remove Clerk | Optional fallback if keys set | |

---

## Fixes applied (this audit)

1. **Important Clauses** — dashboard section added (`important-clauses.tsx`, mapper, tabs).
2. **`/api/v1/public/site`** — no longer 500 when `platform_settings` table missing (defaults fallback).
3. **Unit tests** — 43 tests pass (`test_lite_ai`, `test_public_site`).
4. **`.env` / `.env.example`** — synced; local auth default.

---

## Client demo script (5 min)

```bat
cd d:\Py_Projects\tendoriq
run.bat stop
run.bat
```

1. http://localhost:3000/sign-in → credentials from `.tenderiq/bootstrap-credentials.json` or `/sign-up`  
2. **Upload** → PDF → wait for analysis  
3. **Analysis** → check **Clauses** tab  
4. **Proposal** → Generate  
5. **Analysis** → Export PDF  
6. **Settings** → Billing (demo quota)  
7. **Admin** (admin@tenderiq.com) → optional CMS edit  

---

## What you still configure (not code gaps)

| Item | Action |
|------|--------|
| Migrations | `run.bat` runs `alembic upgrade head` automatically |
| AI analysis | Add `OPENAI_API_KEY` (or other) to `.env` |
| Razorpay upgrade | `RAZORPAY_KEY_ID` + `SECRET` test keys |
| Supabase login | `AUTH_PROVIDER=supabase` + keys — `docs/LOCAL_SETUP.md` |
| R2 production upload | `STORAGE_PROVIDER=r2` + `docs/R2_SETUP.md` |

---

## Automated tests

```bat
cd api
python -m pytest tests/unit -q
```

Expected: **43 passed**, 0 failed.

---

## Sign-off

- **Product:** Matches FINAL MINI PRD for Lite MVP (with documented stack deviations).  
- **Demo:** Ready with local login.  
- **Production:** Follow `docs/DEPLOY.md` + production `.env`.
