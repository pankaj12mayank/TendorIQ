# TenderIQ Lite — Remaining Work Tracker

**Living document.** Har baar kuch complete / block ho, is file ko update karo.  
**Master plan (architecture & phases):** [TENDERIQ_LITE_IMPLEMENTATION_PLAN.md](./TENDERIQ_LITE_IMPLEMENTATION_PLAN.md)

| Field | Value |
|--------|--------|
| **Last updated** | 2026-05-25 |
| **Current focus** | Client demo — see [CLIENT_READY_STATUS.md](./CLIENT_READY_STATUS.md) |
| **Next phase after 10** | — (roadmap complete) |

---

## How to use this file

1. **Done ho** → checkbox `[x]` karo, **Completed on** date likho (optional).
2. **Naya blocker** → **Open blockers** section me add karo.
3. **Phase 100%** → us phase ke header me status `100%` set karo.
4. Git commit message example: `docs: update remaining work — Phase 2 E2E done`

---

## Phase status (summary)

| Phase | Name | Code | E2E / Ops | Overall |
|-------|------|------|-----------|---------|
| 0 | Stabilize | 100% | ~95% | **100%** (Lite scope) |
| 1 | User-scoped DB | 100% | needs migration on your DB | **100%** (scope) |
| 2 | Supabase Auth | ~95% | **blocked — keys + migration** | **~95%** |
| 3 | R2 upload | **100%** | **blocked — R2 bucket + CORS** | **~95%** |
| 4 | AI pipeline | **~95%** | needs API key + upload test | **~95%** |
| 5 | Proposal + company | **~95%** | needs AI key + tender analysis | **~95%** |
| 6 | PDF export only | **~95%** | E2E download test | **~95%** |
| 7 | Demo + Razorpay | **~95%** | needs Razorpay test keys | **~95%** |
| 8 | Admin panel | **~95%** | super admin + migration | **~95%** |
| 9 | Landing + UX | **~95%** | CMS + route cleanup E2E | **~95%** |
| 10 | Cleanup + deploy | **~95%** | Docker + DEPLOY.md | **~95%** |

**Legend:** Code = repo me implementation. E2E/Ops = tumhari machine + Supabase/R2 keys + manual test.

---

## Open blockers (global)

| ID | Blocker | Owner | Unblocks |
|----|---------|-------|----------|
| B1 | Real **Supabase** project URL, anon key, JWT secret in root `.env` + `web/.env.local` | You | Phase 2 E2E |
| B2 | **`alembic upgrade head`** on dev DB (phase1 + phase2 migrations) | You | Phase 1/2 DB columns |
| B3 | `web/`: `pnpm install` (done once) then optional `pnpm typecheck` | You | Phase 0 optional check |
| B4 | Hosted **Supabase Postgres** (PRD) — abhi SQLite/MySQL | Later | Full PRD DB |

---

# Phase 0 — Stabilize

**Status: 100%** (Lite stabilize scope)

### Done
- [x] Analysis `bid_id`, OCR `arq_job_id`, admin `joined_at`, `inline.py`, tenant `Bid` ref
- [x] Real upload (`FileUploader` → API)
- [x] Dead routes, forgot-password, post-login → `/dashboard`
- [x] API unit tests (health, analysis, local_auth, lite_scope, supabase mock)
- [x] Removed fake `UploadTracker` / `simulateUpload`

### Remaining (optional)
- [ ] **P0-OPT-1** Run full `run.bat check` after `cd web && pnpm install`
  - **Steps:**
    1. `cd d:\Py_Projects\tendoriq\web`
    2. `pnpm install`
    3. `cd ..` → `run.bat check`
  - **Done when:** check script green (typecheck warn OK per script)

---

# Phase 1 — User-scoped DB

**Status: 100%** (code). **E2E:** migration on your DB pending if never run.

### Done (code)
- [x] `owner_id`, `company_profiles`, `personal_workspace`, `lite_scope`
- [x] Tenders / files / analysis scoped by user
- [x] `GET/PATCH /api/v1/auth/me/company-profile`
- [x] FE company profile on Settings → Profile
- [x] Migration file: `api/alembic/versions/20260525_phase1_user_scope.py`

### Remaining

| ID | Task | Priority | Steps to complete |
|----|------|----------|-------------------|
| P1-OPS-1 | Apply DB migrations | **High** | 1. Copy `.env.example` → `.env` if needed<br>2. `cd api`<br>3. `venv\Scripts\alembic.exe upgrade head`<br>4. Verify columns: `owner_id`, `company_profiles`, `users.supabase_id` |
| P1-DEFER-1 | Drop `tenants` table | Low (Phase 10) | After R2 + storage path refactor — see Phase 10 |

**Phase 1 = 100%** when **P1-OPS-1** done on your dev DB.

---

# Phase 2 — Supabase Auth

**Status: ~95%** (code done). **E2E blocked on B1 + B2.**

### Done (code)
- [x] `api/src/core/supabase_auth.py`, `supabase_bootstrap.py`
- [x] `POST /api/v1/auth/supabase/session`
- [x] `auth_resolver` verifies Supabase JWT
- [x] `users.supabase_id` + migration `20260525_phase2_supabase_id.py`
- [x] FE: `SupabaseAuthProvider`, sign-up, forgot-password reset
- [x] `.env.example` Supabase variables
- [x] Test: `api/tests/unit/test_supabase_auth.py`

### Remaining (to reach 100%)

| ID | Task | Priority | Steps to complete |
|----|------|----------|-------------------|
| P2-OPS-1 | Create Supabase project | **High** | 1. [supabase.com/dashboard](https://supabase.com/dashboard) → New project<br>2. Authentication → Providers → Email ON<br>3. Note **Project URL**, **anon key**, **JWT Secret** (Settings → API) |
| P2-OPS-2 | Configure `.env` (root) | **High** | Set in `d:\Py_Projects\tendoriq\.env`:<br>`AUTH_PROVIDER=supabase`<br>`SUPABASE_URL=...`<br>`SUPABASE_ANON_KEY=...`<br>`SUPABASE_JWT_SECRET=...`<br>`JWT_SECRET=` (min 32 chars, TenderIQ API tokens) |
| P2-OPS-3 | Configure `web/.env.local` | **High** | `NEXT_PUBLIC_AUTH_PROVIDER=supabase`<br>`NEXT_PUBLIC_SUPABASE_URL=...`<br>`NEXT_PUBLIC_SUPABASE_ANON_KEY=...`<br>`NEXT_PUBLIC_API_URL=http://localhost:8000` |
| P2-OPS-4 | Run migrations | **High** | `cd api` → `venv\Scripts\alembic.exe upgrade head` |
| P2-E2E-1 | Live sign-up | **High** | 1. `run.bat`<br>2. Open `/sign-up` → new email + password<br>3. Confirm email if Supabase requires confirmation<br>4. Land on `/dashboard` |
| P2-E2E-2 | Live sign-in | **High** | Sign out → `/sign-in` → same user → dashboard |
| P2-E2E-3 | Forgot password | Medium | `/forgot-password` → email → reset link works |
| P2-E2E-4 | API session | Medium | Browser network: after login, calls use Bearer TenderIQ JWT; `/api/v1/auth/me` returns user + `company_profile` |
| P2-DEFER-1 | Remove Clerk code paths | Low (Phase 10) | Optional; Clerk still fallback if keys set |

### Verification checklist (tick when done)

- [ ] P2-OPS-1 Supabase project created
- [ ] P2-OPS-2 Root `.env` filled
- [ ] P2-OPS-3 `web/.env.local` filled
- [ ] P2-OPS-4 `alembic upgrade head` OK
- [ ] P2-E2E-1 Sign-up works
- [ ] P2-E2E-2 Sign-in works
- [ ] P2-E2E-3 Password reset works (optional)
- [ ] P2-E2E-4 `/auth/me` + upload API authenticated

**Phase 2 = 100%** when all **Verification checklist** items checked.

---

# Phase 3 — R2 upload (PDF/DOCX 25MB)

**Status: ~95%** (code **100%**). E2E needs your R2 bucket + CORS.

### Done (code)
- [x] **P3-CODE-1** Lite policy: PDF/DOCX only, 25MB (`upload_policy.py`, config defaults)
- [x] **P3-CODE-2** `GET /api/v1/files/upload/config` (provider, limits, `use_presigned`)
- [x] **P3-CODE-3** Presigned flow for `r2`/`s3`; direct upload **local only**
- [x] **P3-CODE-4** Storage keys under `users/{owner_id}/...`
- [x] **P3-CODE-5** FE: `useUploadConfig` + `useFileUpload` presigned-first for cloud
- [x] **P3-CODE-6** Upload page copy + `docs/R2_SETUP.md`
- [x] **P3-CODE-7** Tests: `test_upload_policy.py`

### Remaining (E2E / ops)

| ID | Task | Steps |
|----|------|-------|
| P3-OPS-1 | R2 bucket + API token | See [R2_SETUP.md](./R2_SETUP.md) |
| P3-OPS-2 | Set `STORAGE_PROVIDER=r2` + keys in `.env` | Restart API |
| P3-OPS-3 | Configure **CORS** on R2 bucket | Allow `PUT` from `http://localhost:3000` |
| P3-E2E-1 | Upload PDF via `/dashboard/upload` | initiate → PUT R2 → complete |
| P3-E2E-2 | Reject PNG / 30MB file | UI + API error message |

### Verification checklist

- [ ] P3-OPS-1 R2 bucket created
- [ ] P3-OPS-2 `.env` R2 vars set
- [ ] P3-OPS-3 CORS configured
- [ ] P3-E2E-1 PDF upload succeeds on R2
- [ ] P3-E2E-2 Invalid type/size rejected

**Phase 3 = 100%** when checklist done (or keep `STORAGE_PROVIDER=local` for dev — code path still 100%).

---

# Phase 4 — AI pipeline (multi-provider)

**Status: ~95% code** — E2E needs at least one AI key.

### What shipped

- `GET /api/v1/ai/catalog` — providers + live model list (OpenAI/Ollama)
- `POST /api/v1/ai/test` — connection test
- `POST /api/v1/processing/documents/{id}/analyze` + `retry`
- Auto-analyze on `upload/complete` and `upload/direct`
- Upload UI: provider/model picker + processing status banner

### Steps (you)

| ID | Task |
|----|------|
| P4-OPS-1 | Add **one** of: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, or run Ollama + `OLLAMA_BASE_URL` |
| P4-OPS-2 | Restart API (`run.bat` or uvicorn) |
| P4-E2E-1 | Open `/dashboard/upload` → Test connection → upload PDF |
| P4-E2E-2 | Open analysis link when status = `completed` |

### Verification checklist

- [ ] P4-OPS-1 API key or Ollama configured
- [ ] P4-E2E-1 Catalog shows provider + models
- [ ] P4-E2E-2 Analysis dashboard loads with `tenderId`

---

# Phase 5 — Proposal + company in PDF

**Status: ~95% code** — run migration + AI key + completed analysis first.

### What shipped

- `GET/PATCH /api/v1/auth/me/ai-preferences` (saved in company profile metadata)
- Settings → **AI** page (`/dashboard/settings/ai`)
- `POST /api/v1/proposals/tender/{id}/generate` — lite AI, company profile, analysis context
- `GET /api/v1/proposals/tender/{id}`, section edit, `POST .../export/pdf` with company header
- Proposal UI: generate, edit sections, export PDF
- Analysis page → **Create proposal** link

### Steps (you)

| ID | Task |
|----|------|
| P5-OPS-1 | `alembic upgrade head` (adds `sections_json` on proposals) |
| P5-OPS-2 | Fill **Settings → Company** + **Settings → AI** |
| P5-E2E-1 | Complete Phase 4 analysis for a tender |
| P5-E2E-2 | `/dashboard/proposal?tenderId=` → Generate → Export PDF |

### Verification checklist

- [ ] P5-OPS-1 Migration applied
- [ ] P5-E2E-1 Proposal sections generated
- [ ] P5-E2E-2 PDF shows company name/contact in header

---

# Phase 6 — PDF export only

**Status: ~95% code**

### What shipped

- `LITE_EXPORT_PDF_ONLY=true` — DOCX/HTML/JSON/CSV rejected on legacy export APIs
- `GET /api/v1/exports/config` — PDF only
- `GET /api/v1/exports/tender/{id}/pdf` — direct download (no job queue)
- Analysis report PDF includes **company header** + formatted sections (incl. important clauses)
- Analysis page **Export PDF** button; proposal export remains PDF-only

### Verification checklist

- [ ] P6-E2E-1 Analysis page → Export PDF downloads file
- [ ] P6-E2E-2 PDF shows company name from Settings → Company
- [ ] P6-E2E-3 `GET /exports/formats` returns only `pdf`

---

# Phase 7 — Demo quota + Razorpay

**Status: ~95% code**

### What shipped

- **Demo plan** (`free`) — monthly limits: uploads, AI analyses, proposals, exports
- Usage tracked in `usage_logs`; **402** when quota exceeded
- `GET /api/v1/billing/demo-status` — usage dashboard
- **Razorpay**: `POST /payments/razorpay/create-order`, `POST /payments/razorpay/verify`
- FE **`/dashboard/billing`** — quota cards + plan upgrade (Razorpay Checkout)

### `.env` (API)

```env
RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=xxx
```

### Verification checklist

- [ ] P7-E2E-1 Billing page shows demo usage
- [ ] P7-E2E-2 Upload blocks with 402 after demo limit (optional stress test)
- [ ] P7-E2E-3 Razorpay test payment upgrades plan to Pro

---

# Phase 8 — Admin panel

**Status: ~95% code**

### What shipped

- Removed stale **`apps/api`** folder (duplicate tests / import errors)
- DB table **`platform_settings`** (migration `20260525_phase8_platform`)
- Admin API: `GET/PATCH /api/v1/admin/platform/settings` (pricing, ai_defaults, landing, demo_limits)
- Admin API: `GET /api/v1/admin/platform/uploads` (recent documents)
- Public: `GET /api/v1/public/site` (landing + pricing for homepage)
- Razorpay amounts read from admin **pricing** when set
- Demo quotas merge **demo_limits** from admin settings
- FE **`/dashboard/admin`** — tabs: Overview, Users, Pricing, AI, Landing CMS, Uploads
- Landing page consumes public site content (hero, FAQ, pricing INR, CTA)

### `.env` (super admin)

```env
SUPER_ADMIN_EMAIL=you@example.com
```

Sign in with that email (Clerk or local auth) to access Admin.

### Verification checklist

- [ ] P8-E2E-1 `alembic upgrade head` creates `platform_settings`
- [ ] P8-E2E-2 Admin → edit pricing JSON → landing `/` shows updated INR prices
- [ ] P8-E2E-3 Admin → demo_limits → billing quota reflects new limits
- [ ] P8-E2E-4 Admin → uploads tab lists recent PDFs

---

# Phase 9 — Landing + UX polish

**Status: ~95% code**

### What shipped

- **9-route Lite surface:** `/`, sign-in, sign-up, dashboard, upload, analysis, proposal, settings, admin (+ forgot-password)
- **Settings hub:** profile, AI, billing tabs on `/dashboard/settings` (legacy `/billing`, `/settings/profile`, `/settings/ai` redirect)
- **Sidebar:** billing removed from nav (under Settings)
- **Middleware:** legacy dashboard paths redirect; dead enterprise routes → dashboard
- **Landing:** lean sections (no workflow/demo blocks); CMS for hero, features, testimonials, FAQ, pricing, social proof
- **SEO:** `generateMetadata` from public site API; landing skeleton while loading
- **Navbar:** Sign up CTA; simplified nav anchors

### Verification checklist

- [ ] P9-E2E-1 `/dashboard/billing` → settings billing tab
- [ ] P9-E2E-2 Homepage shows admin-edited hero/pricing after save
- [ ] P9-E2E-3 Sidebar: Upload, Analysis, Proposal, Settings only (no Billing link)
- [ ] P9-E2E-4 View page source / meta title from CMS

---

# Phase 10 — Cleanup + deploy

**Status: ~95% code**

### What shipped

- **Config fix:** `.env` and SQLite path resolve to `tendoriq/` repo root (not `Py_Projects/`)
- **Migration `20260525_phase10_cleanup`:** drops orphan enterprise tables on MySQL/Postgres (skipped on SQLite)
- **`tenants` retained** as personal workspace — not dropped (required by Lite)
- **Docker:** `api/Dockerfile`, `web/Dockerfile` (Next standalone), `docker-compose.yml`
- **Docs:** [DEPLOY.md](./DEPLOY.md) — Railway/Vercel, R2, env checklist
- **`run.bat deploy-check`** — JWT/CORS validation, migrations, full unit tests, Docker file check
- **CI:** runs full `tests/unit` suite
- **`/health/ready`:** database + local storage check

### Verification checklist

- [ ] P10-E2E-1 `run.bat deploy-check` passes
- [ ] P10-E2E-2 `docker compose up --build` → web :3000, API `/health/ready` 200
- [ ] P10-E2E-3 Production `.env`: `NODE_ENV=production`, real `CORS_ORIGINS`, `JWT_SECRET` 32+
- [ ] P10-E2E-4 Hosted deploy smoke: auth → upload → analysis → PDF export

---

# Phase 4–10 — Backlog (short)

Update when each phase starts. See [TENDERIQ_LITE_IMPLEMENTATION_PLAN.md](./TENDERIQ_LITE_IMPLEMENTATION_PLAN.md) §10.

| Phase | One-line remaining |
|-------|-------------------|
| 4 | E2E: add key → upload PDF → `/dashboard/analysis?tenderId=` — code done (multi-provider catalog + auto analyze) |
| 5 | E2E: analysis → generate proposal → PDF (company in header) — code done |
| 6 | E2E: Analysis → Export PDF (company header) — code done |
| 7 | E2E: Billing page + Razorpay test payment — code done |
| 8 | E2E: super admin login → settings → public landing — code done |
| 9 | E2E: settings tabs + landing CMS + legacy redirects — code done |
| 10 | E2E: deploy-check + Docker + DEPLOY.md — code done (`tenants` kept as workspace) |

---

## Quick commands (copy-paste)

```bat
cd d:\Py_Projects\tendoriq\api
venv\Scripts\alembic.exe upgrade head
venv\Scripts\python.exe -m pytest tests\unit\ -q
```

```bat
cd d:\Py_Projects\tendoriq\web
pnpm install
pnpm typecheck
```

```bat
cd d:\Py_Projects\tendoriq
run.bat check
```

---

## Changelog (this file)

| Date | Change |
|------|--------|
| 2026-05-25 | Created tracker; Phase 0–2 remaining + Supabase E2E steps |
| 2026-05-25 | Phase 3 code complete; R2_SETUP.md; E2E checklist added |
| 2026-05-25 | Removed `apps/`; Phase 8 admin CMS + public site + 41 unit tests |
| 2026-05-25 | Phase 9: settings hub, route cleanup, landing CMS polish + SEO |
| 2026-05-25 | Phase 10: deploy Docker/compose, DEPLOY.md, config root fix, phase10 migration |
