# TenderIQ Lite — Complete Implementation Adjustment Plan

> **Status update (2026-05-27):** This roadmap is now largely implemented.  
> For current completion and operational state, refer to:
> - [CLIENT_READY_STATUS.md](./CLIENT_READY_STATUS.md)
> - [TENDERIQ_REMAINING_WORK.md](./TENDERIQ_REMAINING_WORK.md)

**Scope:** Audit of the existing repo vs **FINAL MINI PRD** (implementation roadmap).  
**Constraint:** No new enterprise systems; no queues/Redis/workers; no multi-tenant complexity; no audit/analytics/workflow engines.

> **Living tracker (kya bacha hai + steps):** update regularly → [TENDERIQ_REMAINING_WORK.md](./TENDERIQ_REMAINING_WORK.md)

---

## 1. Existing System Audit

### 1.1 Current architecture (as-is)

```
tendoriq/
├── api/                 # FastAPI (Python 3.12), SQLAlchemy, Alembic
├── web/                 # Next.js 15 App Router (NOT Vite per PRD)
├── scripts/             # run.bat, start/check/gates (keep)
├── run.bat
├── .env.example
└── README.md
```

### 1.2 Frontend audit summary

| Area | PRD-aligned | Notes |
|------|-------------|-------|
| Stack | No | Next.js vs Vite |
| 9 pages | Partial | Extra `/dashboard/settings/profile` |
| Upload | **Broken** | `simulateUpload()` on upload page |
| Auth | No | Clerk/JWT vs Supabase |
| Payment UI | Missing | Broken billing imports |
| Admin | Subset | Users list only |
| Demo mode | Missing | No free-analysis gate |

### 1.3 Backend audit summary

| Area | PRD-aligned | Notes |
|------|-------------|-------|
| DB | No | SQLite/MySQL vs Supabase Postgres |
| Auth | No | Supabase not implemented |
| AI pipeline | **Incomplete** | No upload→OpenAI→store chain |
| Proposal | **Broken** | `ai_service=None`, in-memory only |
| Export | No | Multi-format, not PDF-only |
| Multi-tenant | Conflicts | `tenant_id` everywhere |

**Runtime-breaking issues:** `bid_id` on analysis API; `arq_job_id` on OCR; `Bid` import in `tenant_context`; broken `tasks/inline.py` imports; proposal AI not wired.

---

## 2. PRD Mismatch Analysis (key decisions)

| ID | Mismatch | Decision |
|----|----------|----------|
| M1 | Next.js vs Vite | Keep Next for speed (document deviation) unless contractual |
| M2 | Supabase Auth | **Rebuild** (Phase 2) |
| M3 | Supabase Postgres | **Rebuild** (Phase 1) |
| M4 | Multi-tenant | **Remove** (Phase 1) |
| M6 | Fake upload | **Rebuild** (Phase 0 + 3) |
| M7 | No AI pipeline | **Rebuild** (Phase 4) |
| M8 | Proposal disconnected | **Rebuild** (Phase 5) |
| M10 | Razorpay | **Build** (Phase 7) |
| M21 | Schema/API drift | **Fix** (Phase 0) |

---

## 3. Removal Plan

**Backend remove:** Gemini/Ollama providers, OCR routes (or internal only), Stripe webhook, duplicate files/documents API (later), `tenant_context` Bid refs, legacy `core/ai.py`, onboarding schemas, mock admin_auth services.

**Frontend remove:** Enterprise landing blocks, complex RBAC, tenant-store, broken billing hooks, fake pipeline, Clerk (after Phase 2), dead nav routes.

**DB drop (later phases):** tenants, memberships, ocr_*, queue, audit, email tables, prompt_versions, ai_providers.

---

## 4. Refactor Plan

Reuse: analysis UI sections, PDF generator, parsers, shadcn UI, `run.bat` scripts.  
Rewrite: auth, DB scoping, upload wiring, processing orchestrator, proposal service, admin panel, landing CMS.  
Do not add microservices or queues.

---

## 5. Missing Features (PRD)

P0: Supabase auth, real upload, AI pipeline, validation/retry, proposal, PDF export, usage/demo/Razorpay, admin users+AI settings.  
P1: Company profile, admin pricing/landing CMS, emails, UX polish.

---

## 6. Database Refactor Plan (target)

`users`, `company_profiles`, `platform_settings`, `site_content`, `tenders`, `tender_analysis`, `proposals`, `usage_records`, `payments` — user-scoped, no `tenant_id`.

---

## 7. Frontend Refactor Plan

**Keep 9 routes:** `/`, login, signup, dashboard, upload, analysis, proposal, settings, admin.  
**Remove:** tenders/bids/documents/billing sub-routes, onboarding, extra profile route (merge into settings).

---

## 8. Backend Refactor Plan

**Target APIs:** health, auth/me, tenders (upload/process/retry), analysis, proposal, PDF export, usage, Razorpay, admin settings/users/uploads.

---

## 9. Final Simplified Architecture

```
tendoriq/
├── api/src/          # FastAPI, flat routers around tenders
├── web/src/          # 9 pages, Supabase client (Phase 2)
└── scripts/
```

---

## 10. Implementation Roadmap

| Phase | Objective | Est. |
|-------|-----------|------|
| **0** | Stabilize: fix 500s, real upload wire, dead routes | 1–2d |
| **1** | User-scoped DB, drop tenant | 3–5d |
| **2** | Supabase Auth | 3–4d |
| **3** | R2 upload PDF/DOCX 25MB | 2–3d |
| **4** | Processing + OpenAI analysis | 5–7d |
| **5** | Proposal + company profile | 3–4d |
| **6** | PDF export only | 2d |
| **7** | Demo + Razorpay + usage | 4–5d |
| **8** | Full admin panel | 4–5d |
| **9** | Landing + UX polish | 2–3d |
| **10** | Cleanup + deploy | 2–3d |

---

## 11. Remaining Scope Verification

**Not covered without explicit approval:** Vite migration (default: keep Next).  
**Must add in Phase 4 schema:** "important clauses" analysis section.  
**Intentionally excluded:** Redis, ARQ, audit, analytics engine, enterprise RBAC, DOCX export, subscription automation.

---

*Document generated from full gap analysis. Implement in phase order; do not skip Phase 0.*

---

## Phase 0 checklist (stabilize)

- [x] Save this plan under `docs/`
- [x] Remove `bid_id` from analysis API
- [x] Remove `arq_job_id` from OCR responses/schemas
- [x] Fix admin membership `joined_at`
- [x] Fix `tasks/inline.py` (OCR only, no dead queue/email imports)
- [x] Remove broken `Bid` reference in `tenant_context`
- [x] Wire upload page to real `FileUploader` + API
- [x] Stub missing FE modules (`tenant-workspace`, `onboarding-api`, billing types)
- [x] Fix dashboard dead links; add `/forgot-password` page
- [x] Post-login → `/dashboard` (no `/onboarding` redirect)
- [x] API import + unit tests pass (`pytest` health, analysis, local_auth)
- [x] `conftest.py` uses `NODE_ENV=development` (valid for Settings)
- [x] Dead `UploadTracker` / `simulateUpload` removed (use `FileUploader` only)
- [ ] Run full `run.bat check` after `pnpm install` in `web/` (typecheck needs deps) → track in [REMAINING_WORK](./TENDERIQ_REMAINING_WORK.md#phase-0--stabilize)

**Phase 0 status: 100% complete** for Lite stabilize scope.

---

## Phase 1 checklist (user-scoped DB)

- [x] `OwnerMixin` + `owner_id` on tenders, documents, analysis, proposals
- [x] `company_profiles` table + Alembic migration `20260525_phase1_user`
- [x] `personal_workspace` bootstrap (auto workspace per user)
- [x] `lite_scope` query helpers + `require_lite_user` dependency
- [x] Tenders / files / analysis APIs scoped by `owner_id`
- [x] `GET/PATCH /api/v1/auth/me/company-profile`
- [x] FE: `hasTenantWorkspace` = authenticated user; company profile hook
- [ ] Drop legacy `tenants` table (Phase 10) → [REMAINING_WORK](./TENDERIQ_REMAINING_WORK.md#phase-1--user-scoped-db)

**Phase 1 status: 100% complete** for Lite user-scoping scope (tenant table retained by design). Ops: [P1-OPS-1](./TENDERIQ_REMAINING_WORK.md#phase-1--user-scoped-db).

---

## Phase 2 checklist (Supabase Auth)

- [x] API: `SUPABASE_*` settings + JWT verify (`supabase_auth.py`)
- [x] API: user bootstrap `supabase_id` + `ensure_supabase_user`
- [x] API: `POST /api/v1/auth/supabase/session` token exchange
- [x] API: `auth_resolver` accepts Supabase JWT
- [x] Migration: `users.supabase_id`
- [x] FE: `@supabase/supabase-js` + browser client
- [x] FE: `SupabaseAuthProvider` (sign-in / sign-up / session sync)
- [x] FE: forgot-password via `resetPasswordForEmail`
- [x] `.env.example` Supabase vars + `AUTH_PROVIDER=supabase`
- [x] Unit test `test_supabase_auth.py`
- [ ] **Requires your Supabase project keys in `.env`** — then E2E sign-up/sign-in → **[REMAINING_WORK Phase 2](./TENDERIQ_REMAINING_WORK.md#phase-2--supabase-auth)**
- [ ] Remove Clerk paths (optional cleanup Phase 10; Clerk still works as fallback)

**Phase 2 code status: ~95%** — implementation complete; **100% E2E:** follow [TENDERIQ_REMAINING_WORK.md](./TENDERIQ_REMAINING_WORK.md) verification checklist.

---

## Phase 3 checklist (R2 upload)

- [x] PDF/DOCX only, 25MB (API + FE)
- [x] Presigned upload for `r2`/`s3`; direct for `local`
- [x] `GET /api/v1/files/upload/config`
- [x] User-scoped storage keys `users/{owner_id}/...`
- [x] [R2_SETUP.md](./R2_SETUP.md)
- [ ] R2 bucket + CORS + live upload → [REMAINING_WORK](./TENDERIQ_REMAINING_WORK.md#phase-3--r2-upload-pdfdocx-25mb)

**Phase 3 code: 100%.** E2E: set `STORAGE_PROVIDER=r2` or stay on `local` for dev.
