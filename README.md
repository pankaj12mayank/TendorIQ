# TenderIQ Lite

AI-assisted tender workflow for teams: upload RFP documents, run structured analysis, draft proposals, and export results. This repository is the **Lite MVP** — a focused stack you can run locally without cloud auth or paid services.

| Layer | Technology |
|-------|------------|
| API | Python 3.12+, FastAPI, SQLAlchemy, Alembic |
| Web | Node 20+, Next.js 15, React 19, Tailwind CSS |
| Database (dev) | SQLite (file under `.tenderiq/data/`) |
| Database (prod) | MySQL or PostgreSQL |
| Auth (dev default) | Database email/password (`AUTH_PROVIDER=local`) |

---

## Features (Lite SaaS)

- **Landing & marketing CMS** — draft/publish/rollback, customer stories, workflow steps, branding assets
- **Authentication & sessions** — local auth with JWT + refresh, HttpOnly cookie-first flow, inactivity controls
- **Real user dashboard** — plan/expiry/usage cards, restriction banners, quick actions, user-scoped tenders
- **Upload & analysis** — PDF/DOCX ingestion, AI summary/compliance/clauses, retry-safe processing
- **Proposal builder** — sectioned proposal generation + PDF export
- **Monetization** — yearly-only plans, usage/expiry restrictions, payment history
- **Owner control center** — pricing/plans, support email, CMS, users (suspend/soft delete/restore), uploads, payments, analytics

---

## Prerequisites

Install before first run:

| Tool | Version |
|------|---------|
| [Python](https://www.python.org/downloads/) | 3.11 or newer |
| [Node.js](https://nodejs.org/) | 20 or newer |
| [pnpm](https://pnpm.io/) | 9+ (`npm install -g pnpm`) |

Windows users: run commands from **cmd** or PowerShell. `run.bat` wraps the setup scripts in `scripts/`.

---

## Quick start

From the repository root:

```bat
copy .env.example .env
run.bat
```

> `run.bat` automatically creates `web/.env.local` from root `.env` — no manual copy needed.

On first start, `run.bat` will:

1. Create or repair `api/venv` and install Python dependencies
2. Install web dependencies when needed (`web/node_modules`)
3. Apply database migrations (SQLite at `.tenderiq/data/tenderiq.db`)
4. Seed system owner + demo user accounts
5. Start the API on **http://localhost:8000** and the web app on **http://localhost:3000**

Open **http://localhost:3000/sign-in**.

### Sign-in (database only)

Login passwords are **not** stored in `.env`. Use one of:

1. **First run** — after `run.bat`, open `.tenderiq/bootstrap-credentials.json` for one-time bootstrap accounts (gitignored).
2. **Register** — http://localhost:3000/sign-up (password min. 8 characters).

Supabase and Clerk are optional in this Lite stack. OpenAI/AI provider keys are optional for analysis features.

### Troubleshooting login

If login returns an HTML error — stop the servers, delete the dev database, and restart:

```bat
run.bat stop
del /q .tenderiq\data\tenderiq.db 2>nul
run.bat
```

---

## Project structure

```
tendoriq/
├── api/                 # FastAPI application, Alembic migrations, unit tests
├── web/                 # Next.js frontend
├── scripts/             # PowerShell helpers (startup, check, deploy)
├── docs/                # Setup, deploy, and implementation notes
├── .tenderiq/           # Local runtime data (SQLite DB, logs) — gitignored
├── run.bat              # One-click dev: start, stop, check, setup
├── .env.example         # Environment template (API + shared config)
└── docker-compose.yml   # Optional containerized stack
```

The legacy `apps/` directory is **not** used. If it still exists on disk from an older checkout, stop servers (`run.bat stop`) and delete it to avoid confusion.

---

## Commands (`run.bat`)

| Command | Description |
|---------|-------------|
| `run.bat` | Start API + web (development) |
| `run.bat stop` | Stop background API and web processes |
| `run.bat check` | Verify imports, unit tests, migrations (no servers) |
| `run.bat setup` | Force dependency reinstall and full startup |
| `run.bat deploy-check` | Production readiness (env, migrations, tests) |
| `run.bat e2e` | Playwright E2E (requires stack running) |
| `run.bat gates` | Client-ready gate script (G0–G5) |

Logs: `.tenderiq/startup.log`, `api.log`, `web.log`.

---

## Configuration

All shared settings live in the **repository root** `.env`. The web app reads public variables via `web/.env.local` (synced automatically on startup).

| Variable | Purpose |
|----------|---------|
| `AUTH_PROVIDER` | `local` (default), `supabase`, or `clerk` |
| `DATABASE_DRIVER` | `sqlite` (default dev) or `mysql` |
| `JWT_SECRET` | API session signing (32+ characters) |
| `OPENAI_API_KEY` | Optional — enables AI analysis |

Keep `.env` and `.env.example` in sync when adding keys. Details: **[docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md)**.

---

## Development

### API

```bat
cd api
venv\Scripts\python.exe -m pytest tests\unit -q
venv\Scripts\python.exe -m uvicorn src.main:app --reload --port 8000
```

Dependencies: `api/requirements.txt` (runtime) and `api/requirements-dev.txt` (pytest, ruff, mypy).

### Web

```bat
cd web
pnpm install
pnpm dev
```

### Health endpoints

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | OpenAPI (Swagger) |
| http://localhost:8000/health | Liveness |
| http://localhost:8000/health/ready | Readiness (DB + storage) |

---

## Deployment

Production setup (Docker, MySQL/Postgres, R2 storage, Supabase auth): **[docs/DEPLOY.md](docs/DEPLOY.md)**.

```bat
run.bat deploy-check
docker compose up --build
```

Migrations run automatically in the API container on startup.

**Lite database note:** The `tenants` table is used as personal workspace context (retained in Lite). Cleanup migrations remove unused enterprise-only tables on MySQL/PostgreSQL; SQLite skips destructive drops where unsupported.

---

## Troubleshooting

### Login returns 503 or “schema is out of date”

SQLite was missing columns because migrations were skipped. Fix:

```bat
run.bat stop
cd api
venv\Scripts\python.exe -m alembic upgrade head
cd ..
run.bat
```

### `ChunkLoadError` on `app/layout.js`

Usually caused by clearing `.next` while the dev server is running. Fix:

```bat
run.bat stop
run.bat
```

Hard refresh the browser (Ctrl+Shift+R). Full cache clear only when needed: `run.bat setup`.

### `pip install` fails with `apps\api\venv`

The virtualenv was created before the move from `apps/api` to `api/`. Fix:

```bat
run.bat stop
rmdir /s /q api\venv
run.bat setup
```

Or simply run `run.bat` — startup detects a broken venv and recreates `api/venv` automatically.

### `Next.js not available after pnpm install`

Broken or partial `web/node_modules` (often after moving folders). Fix:

```bat
cd web
pnpm install
cd ..
run.bat
```

### `run.bat check` fails on migrations

Ensure `.env` uses `DATABASE_DRIVER=sqlite` for local dev. Delete a corrupted dev DB only if you accept losing local data:

```bat
del .tenderiq\data\tenderiq.db
run.bat check
```

### Port already in use

```bat
run.bat stop
```

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) | Env files, local auth, optional Supabase/Clerk |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Production deploy and Docker |
| [docs/TENDERIQ_REMAINING_WORK.md](docs/TENDERIQ_REMAINING_WORK.md) | Current completion and remaining ops checklist |
| [docs/CLIENT_READY_STATUS.md](docs/CLIENT_READY_STATUS.md) | Current readiness, risks, and audit snapshot |

---

## Support

For implementation history and PRD alignment, see `docs/`. Report issues with steps to reproduce, `.tenderiq/startup.log` excerpts, and the output of `run.bat check`.
