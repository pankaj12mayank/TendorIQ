# Testing

## API (pytest)

From `apps/api`:

```bash
pytest tests/unit tests/integration -q
```

`tests/conftest.py` sets default `DATABASE_URL`, `JWT_SECRET`, and `RATE_LIMIT_ENABLED=false` so unit tests stay quiet without Redis.

Contract tests:

- `tests/contracts/fe_api_paths.json` — paths the web app expects
- `tests/unit/test_openapi_contract.py` — asserts those paths exist in `/openapi.json`

Layer regression (audit L0–L13):

```bash
pytest tests/unit/test_layer*.py -q
```

`run.bat check` runs the same layer tests plus compile, import, MySQL, and migrations.

## Web (Vitest)

```bash
pnpm --filter @tendoriq/web test -- --run
```

Includes `api-contract.test.ts`, `auth-unauthorized.test.ts` (401 → sign-in redirect), and hook helper tests.

## E2E (Playwright)

**Public routes** (web only, e.g. CI preview):

```bash
pnpm --filter @tendoriq/web exec playwright test --project=chromium
```

**Authenticated flows** (API `:8000` + web `:3000`):

```bash
run.bat          # start stack
run.bat e2e      # or: scripts/tenderiq-e2e.ps1
```

Setup projects call `POST /api/v1/auth/login` and save `e2e/.auth/demo.json` and `admin.json`.  
Credentials default from `.env` (`DEMO_USER_*`, `SUPER_ADMIN_*`).

Specs:

- `e2e/public-routes.spec.ts` — sign-in, landing, unauthenticated redirects
- `e2e/authenticated-flows.spec.ts` — tenant tenders/upload/review + admin console

## Client-ready sign-off

See [CLIENT_READY.md](CLIENT_READY.md) for the full manual smoke table.

## CI

- `.github/workflows/ci.yml` — lint, API pytest with **MySQL service** + `alembic upgrade head`, web Vitest
- `.github/workflows/automated-tests.yml` — coverage, integration (MySQL), E2E preview
