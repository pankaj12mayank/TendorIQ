# Client-ready sign-off checklist

Use this after **`run.bat check`** passes and the stack is running (`run.bat`).

## Automated gates

| Gate | Command | Pass criteria |
|------|---------|---------------|
| **G0-G5 (full)** | **`run.bat gates`** | MySQL, check, migrations, stack, API smoke, Playwright |
| G1 only | `run.bat check` | All layer tests L0-L13, compile, import, MySQL, migrations |
| API unit + integration | `cd apps/api && pytest tests/unit tests/integration -q` | Green (CI: MySQL service + `alembic upgrade head`) |
| Web unit | `pnpm --filter @tendoriq/web test -- --run` | Green (includes 401 redirect test) |
| E2E (public) | `pnpm --filter @tendoriq/web e2e -- --project=chromium` | Green with web on :3000 |
| E2E (authenticated) | `run.bat e2e` | API :8000 + web :3000; demo + admin login flows |

## Manual smoke (required for L12-10)

Run with `DEMO_USER_*` or your tenant account after `run.bat`:

| # | Flow | Steps | Expected |
|---|------|-------|----------|
| 1 | Sign-in | `/sign-in` → demo credentials | Lands on dashboard or onboarding |
| 2 | Tenders | Dashboard → Tenders | List or empty state loads (no infinite spinner) |
| 3 | Upload | Dashboard → Upload | Page loads; upload UI visible |
| 4 | Review | Open review with `?tenderId=` | Session loads or clear error |
| 5 | Billing | `/dashboard/billing` | Plans/usage from API |
| 6 | Super admin | Super admin → `/dashboard/admin` | Users / queue modules load |
| 7 | Email | Admin → Email System | Templates list or empty |
| 8 | Health | `GET /health` and `/health/ready` | `healthy`; ready 200 when DB up |

## Environment

- MySQL 8+, `DATABASE_URL` in `.env` — [MYSQL_SETUP.md](MYSQL_SETUP.md)
- `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD` for platform console
- `DEMO_USER_EMAIL` / `DEMO_USER_PASSWORD` for tenant E2E

## Not client-ready if

- Review page spins forever without `tenderId`
- Billing or usage shows only mock/random data
- Admin tabs 404 on platform APIs
- `run.bat check` fails on migrations or layer contract tests

Track audit progress: [AUDIT_STATUS.md](AUDIT_STATUS.md).
