# Testing

## API (pytest)

From `apps/api`:

```bash
pytest tests/unit tests/integration -q
```

`tests/conftest.py` sets default `DATABASE_URL` and `JWT_SECRET` so unit tests do not require a local `.env`.

Contract tests:

- `tests/contracts/fe_api_paths.json` — paths the web app expects
- `tests/unit/test_openapi_contract.py` — asserts those paths exist in `/openapi.json` (skips if optional deps like `svix` are missing locally)

## Web (Vitest)

```bash
pnpm --filter @tendoriq/web test -- --run
```

Includes `api-contract.test.ts` (reads the shared JSON contract) and hook helper tests.

## E2E (Playwright)

```bash
pnpm --filter @tendoriq/web e2e
```

`e2e/public-routes.spec.ts` covers sign-in, landing, and unauthenticated dashboard redirect.

## CI

`.github/workflows/ci.yml` runs API pytest and web Vitest on pull requests.  
`.github/workflows/automated-tests.yml` runs extended suites (coverage, E2E, security audit).
