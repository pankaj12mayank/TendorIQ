# TenderIQ Local Setup Guide

## Quick Start (recommended)

### Prerequisites

1. **Python 3.12+** — https://www.python.org/downloads/ (check “Add to PATH”)
2. **Node.js 20+** — https://nodejs.org/ (pnpm via corepack)
3. **MySQL 8+** — https://dev.mysql.com/downloads/ (Windows service running)

No PostgreSQL, Redis, or Docker required for local dev.

### Steps

```batch
git clone <your-repo-url>
cd tenderiq
copy .env.example .env
```

Edit `.env` and set **`DATABASE_URL`** with your real MySQL password:

```env
DATABASE_URL=mysql+aiomysql://root:YOUR_PASSWORD@localhost:3306/tenderiq?charset=utf8mb4
```

Then:

```batch
run.bat
```

`run.bat` automatically:

- Creates `venv` and installs Python/Node dependencies
- Checks MySQL connectivity
- Creates the `tenderiq` database if missing
- Runs **`alembic upgrade head`**
- Starts API (`:8000`) and web (`:3000`)

Sign in at http://localhost:3000/sign-in using `SUPER_ADMIN_*` or `DEMO_USER_*` from `.env`.

Use **`run.bat check`** for compile + import + MySQL + migrations without starting servers.

---

## Manual setup

```bash
cd apps/api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd ../..
copy .env.example .env
# edit DATABASE_URL
cd apps/api
set DOTENV_PATH=../../.env
python scripts/ensure_mysql.py
python -m alembic upgrade head
uvicorn src.main:app --reload --port 8000
```

Frontend (second terminal, repo root):

```bash
pnpm install
pnpm --filter @tendoriq/web run dev
```

See [MYSQL_SETUP.md](./MYSQL_SETUP.md) and [database-migrations.md](./database-migrations.md).

---

## Troubleshooting

### MySQL connection failed

1. Start the **MySQL** Windows service (Services app or `net start MySQL80`).
2. Confirm password in `.env` matches your MySQL user.
3. Run `run.bat check` — step `[3/5] MySQL reachability` must pass.
4. Create DB manually if needed:

```sql
CREATE DATABASE tenderiq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Migrations failed

From `apps/api` with `DOTENV_PATH` pointing at repo `.env`:

```bash
python -m alembic upgrade head
```

### Port already in use

```batch
run.bat stop
```

### Python / Node not found

Install Python 3.12+ and Node 20+, then re-run `run.bat`.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `run.bat` | Full bootstrap: deps, MySQL, migrations, start stack |
| `run.bat check` | L0 gates without starting servers |
| `run.bat setup` | Force reinstall dependencies + start |
| `run.bat stop` | Stop API and web |

---

## Services (local)

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Next.js |
| Backend API | 8000 | FastAPI |
| MySQL | 3306 | Database |

---

## Access

- Frontend: http://localhost:3000  
- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  
