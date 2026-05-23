# Deployment Guide

> **Stack:** MySQL 8+ for persistence. Background work (email, OCR) uses **in-process** `core.tasks.inline` — **Redis and ARQ are not required**.  
> **Local dev:** use `run.bat` (see [local-setup.md](local-setup.md) and [MYSQL_SETUP.md](MYSQL_SETUP.md)).

---

## Prerequisites

- [ ] **MySQL 8+** (managed or self-hosted)
- [ ] Domain + TLS (production)
- [ ] `JWT_SECRET` (32+ characters) and other secrets from [.env.production.example](../.env.production.example)
- [ ] Optional: **Redis** only if you enable distributed rate limiting (`RATE_LIMIT_ENABLED` + Redis client wiring)

---

## Environment

Copy `.env.production.example` → `.env` (or set variables in Railway/Vercel).

```env
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/tenderiq?charset=utf8mb4
JWT_SECRET=<32-char-minimum>
FRONTEND_URL=https://app.example.com
API_URL=https://api.example.com
CORS_ORIGINS=https://app.example.com
```

Email, Stripe, AI keys: see [environment-config.md](environment-config.md).

---

## Local / Windows (recommended for developers)

```batch
copy .env.example .env
REM Set DATABASE_URL to your MySQL password
run.bat
```

- **`run.bat check`** — compile, import, MySQL, `alembic upgrade head` (no servers)
- **`run.bat stop`** — stop API and web

No `docker compose up` required for day-to-day development.

---

## Production options

### Option 1: Railway / managed API + MySQL

1. Provision **MySQL** (Railway plugin, PlanetScale, RDS, etc.).
2. Set `DATABASE_URL` with the `mysql+aiomysql://` driver.
3. Deploy API from `apps/api` (`requirements.txt`, `uvicorn src.main:app`).
4. Deploy web to Vercel with `NEXT_PUBLIC_API_URL`.

### Option 2: Docker (API + MySQL only)

```bash
docker compose up -d mysql api
```

Optional Redis (rate limiting experiments):

```bash
docker compose --profile with-redis up -d
```

Build API image manually (`apps/api/Dockerfile` uses `apps/api/requirements.txt`):

```bash
docker build -t tendoriq-api apps/api
docker run -d -p 8000:8000 --env-file .env.production tendoriq-api
```

Health: `GET /health`.

### Option 3: Vercel (frontend) + hosted MySQL API

1. Connect repo to Vercel for `apps/web`.
2. Point `NEXT_PUBLIC_API_URL` at your API host.
3. Run migrations on the API host before traffic:

```bash
cd apps/api
python -m alembic upgrade head
```

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

## Frontend

```bash
cd apps/web
pnpm install
pnpm build
# Vercel: pnpm exec vercel --prod
```

---

## Post-deployment checklist

- [ ] `GET /health` → 200
- [ ] `DATABASE_URL` uses MySQL driver (`mysql+aiomysql` or `mysql+pymysql` for Alembic sync URL)
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

See [scaling-strategy.md](scaling-strategy.md) for roadmap notes (some diagrams are aspirational).

---

## Backup

```bash
mysqldump -h HOST -u USER -p tenderiq > backup-$(date +%Y%m%d).sql
```

---

## Troubleshooting

See [troubleshooting.md](troubleshooting.md).
