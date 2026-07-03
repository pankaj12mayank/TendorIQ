# TenderIQ Lite — Deploy Guide

Production deploy for the **9-route MVP**: landing, auth, dashboard, upload, analysis, proposal, settings (incl. billing), admin.

Business model in current Lite build is **yearly pricing only** (no monthly plans).

## Architecture

| Service | Stack | Default port |
|---------|--------|--------------|
| API | FastAPI + Uvicorn | 8000 |
| Web | Next.js (standalone) | 3000 |
| DB | SQLite (dev) or **MySQL / Postgres** (hosted) | — |
| Files | Local disk or **Cloudflare R2** | — |

The `tenants` table is **kept** in Lite: each user gets a personal workspace row (`personal_workspace` bootstrap). Phase 10 migrations only drop unused *enterprise* tables, not `tenants`.

---

## 1. Environment

Copy root `.env.example` → `.env` and set at minimum:

```env
NODE_ENV=production
JWT_SECRET=<32+ random chars>
ENCRYPTION_KEY=<32+ random chars>

# Auth (pick one)
AUTH_PROVIDER=supabase
SUPABASE_URL=...
SUPABASE_JWT_SECRET=...
NEXT_PUBLIC_AUTH_PROVIDER=supabase
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...

# URLs
FRONTEND_URL=https://app.yourdomain.com
APP_URL=https://app.yourdomain.com
API_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_URL=https://app.yourdomain.com
CORS_ORIGINS=https://app.yourdomain.com

# Database (production)
DATABASE_DRIVER=mysql
MYSQL_HOST=...
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DATABASE=tenderiq

# Storage (production)
STORAGE_PROVIDER=r2
STORAGE_BUCKET=tendoriq-uploads
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
STORAGE_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com

# Super admin
# Create a platform admin user in the database (preferences.platform_super_admin=true)

EXPOSE_ERROR_DETAILS=false
RELOAD=false
WORKERS=2
```

See [R2_SETUP.md](./R2_SETUP.md) for bucket CORS.

---

## 2. Database migrations

On every API deploy run:

```bash
cd api
alembic upgrade head
```

Head includes Phase 10 cleanup (`20260525_phase10_cleanup`) on MySQL/Postgres only.

---

## 3. Split deploy

### API — Railway / Render / Fly

1. Root directory: `api/`
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. Set env from section 1; attach persistent volume for `SQLITE_PATH` / `STORAGE_LOCAL_PATH` if using SQLite.
5. For MySQL, use host's managed DB URL via `DATABASE_DRIVER=mysql`.
6. Health check path: `/health/ready`

### Web — Vercel / any Node host

1. Root directory: `web/`
2. Framework: Next.js
3. Build: `pnpm build` (or enable default)
4. Env: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_APP_URL`, Supabase public keys
5. Do **not** expose `JWT_SECRET` on Vercel — API only.

---

## 4. Pre-deploy checklist

Run locally:

```powershell
pnpm test:api
```

| Check | Command / URL |
|-------|----------------|
| Migrations | `alembic upgrade head` |
| Unit tests | `pytest tests/unit -q` |
| API ready | `curl https://api.../health/ready` |
| CORS | Upload from web origin |
| Razorpay | Test keys + Billing tab upgrade |
| Platform admin | DB user with `platform_super_admin` → `/dashboard/admin` |

---

## 5. Post-deploy smoke test

1. Sign up / sign in  
2. Upload PDF → Analysis  
3. Create proposal → Export PDF  
4. Settings → Billing (demo quota)  
5. Homepage loads CMS from `GET /api/v1/public/site`
6. Owner `/dashboard/admin` can manage users (suspend, soft delete, restore) and CMS publish flow

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| 502 on upload | R2 CORS + `STORAGE_PROVIDER` |
| 401 on API | `CORS_ORIGINS`, cookie/`Authorization` from web URL |
| Migrations fail on SQLite | Phase 10 drops are skipped on SQLite — safe |
| Wrong `.env` loaded | API loads repo root `.env` (`tendoriq/.env`) |
