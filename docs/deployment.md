# Deployment Guide

> **Stack:** MySQL 8+ for persistence. Background work (email, OCR) uses **in-process** `core.tasks.inline` — **Redis and ARQ are not required**.  
> **Local dev:** `run.bat` only — no Docker ([local-setup.md](local-setup.md), [MYSQL_SETUP.md](MYSQL_SETUP.md)).

---

## Prerequisites

- [ ] **MySQL 8+** (managed: PlanetScale, Railway MySQL, Aiven, RDS, etc.)
- [ ] Domain + TLS (production)
- [ ] `JWT_SECRET` (32+ characters) and other secrets from [.env.production.example](../.env.production.example)
- [ ] Optional: **Redis** only if you enable distributed rate limiting

---

## Environment

Copy `.env.production.example` → platform env vars (Railway, Porter, Vercel).

```env
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/tenderiq?charset=utf8mb4
JWT_SECRET=<32-char-minimum>
FRONTEND_URL=https://app.example.com
API_URL=https://api.example.com
CORS_ORIGINS=https://app.example.com
```

Email, Stripe, AI keys: see [environment-config.md](environment-config.md).

---

## Local / Windows (developers)

```batch
copy .env.example .env
REM Set DATABASE_URL to your local MySQL password
run.bat
```

- **`run.bat check`** — compile, import, MySQL, `alembic upgrade head` (no servers)
- **`run.bat stop`** — stop API and web

---

## Production (recommended layout)

| Component | Host | Notes |
|-----------|------|--------|
| **Web** | **Vercel** | `apps/web`, set `NEXT_PUBLIC_API_URL` |
| **API** | **Railway / Porter / Render** | `apps/api`, Python + `requirements.txt` |
| **MySQL** | Managed DB | Connection string in API `DATABASE_URL` |

### API on Railway / Porter (no Docker)

1. Create a service with root directory **`apps/api`**.
2. Build: `pip install -r requirements.txt` (see `apps/api/railway.json` for Nixpacks defaults).
3. Start: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. Set `DATABASE_URL` to hosted MySQL (`mysql+aiomysql://...`).
5. Run migrations once:

```bash
cd apps/api
set DOTENV_PATH=../../.env.production
python -m alembic upgrade head
```

### Frontend on Vercel

1. Connect repo; set root to **`apps/web`** (or monorepo filter `@tendoriq/web`).
2. `NEXT_PUBLIC_API_URL` → your API URL.
3. Deploy.

Health: `GET /health` on the API host.

---

## Database migrations

```bash
cd apps/api
set DOTENV_PATH=../../.env   # Windows
export DOTENV_PATH=../../.env # Linux/macOS
python -m alembic upgrade head
```

See [database-migrations.md](database-migrations.md).

---

## Frontend build

```bash
cd apps/web
pnpm install
pnpm build
```

---

## Post-deployment checklist

- [ ] `GET /health` → 200
- [ ] `DATABASE_URL` uses MySQL driver (`mysql+aiomysql`)
- [ ] `alembic upgrade head` succeeded on production DB
- [ ] Sign-in and tenant flows work
- [ ] Stripe webhook URL configured (if billing enabled)
- [ ] Sentry DSN set (optional)

---

## Scaling (current vs future)

| Today | Future (optional) |
|-------|-------------------|
| Inline email/OCR jobs in API process | Dedicated worker process |
| MySQL connection pool in SQLAlchemy | Read replicas |
| In-memory / DB-backed queue tables | Redis for distributed rate limits |

See [scaling-strategy.md](scaling-strategy.md).

---

## Backup

```bash
mysqldump -h HOST -u USER -p tenderiq > backup-$(date +%Y%m%d).sql
```

---

## Troubleshooting

See [troubleshooting.md](troubleshooting.md).
