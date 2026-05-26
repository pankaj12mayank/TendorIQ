# TenderIQ Lite

```
tendoriq/
├── api/          # FastAPI backend
├── web/          # Next.js frontend
├── scripts/      # run.bat helpers (keep)
├── run.bat       # start / stop / check
├── .env.example
└── README.md
```

## Quick start (no cloud keys)

```bat
copy .env.example .env
copy web\.env.local.example web\.env.local
run.bat
```

Sign in: **demo@tendoriq.com** / **Demo@123** (or admin — see [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md))

- Web: http://localhost:3000  
- API: http://localhost:8000  
- Stop: `run.bat stop`  
- Check: `run.bat check`

## First-time web deps

```bat
cd web
pnpm install
```

## MVP pages

Landing, Sign-in, Sign-up, Dashboard, Upload, Analysis, Proposal, Settings, Admin.

## Deploy (production)

See **[docs/DEPLOY.md](docs/DEPLOY.md)** for Railway/Vercel, R2, and MySQL.

```bat
run.bat deploy-check
docker compose up --build
```

- API health: `GET /health/ready` (database + local storage)
- Migrations run automatically in the API Docker image

## Commands

| Command | Purpose |
|---------|---------|
| `run.bat` | Start API + web (dev) |
| `run.bat stop` | Stop servers |
| `run.bat check` | Import + migrations + unit tests |
| `run.bat deploy-check` | Production readiness gate |

## Note

If an old `apps/` folder remains, stop servers (`run.bat stop`) and delete `apps/` manually — it is a leftover from the previous monorepo layout.

**Lite DB note:** The `tenants` table is your per-user workspace (not removed in Phase 10). Enterprise-only tables are dropped via Alembic on MySQL/Postgres.
