# Monorepo & tooling

TenderIQ is a **pnpm + Turbo** monorepo. Python API dependencies are managed separately via `apps/api/requirements.txt` (and `uv` in CI).

## Layout

| Path | Package | Purpose |
|------|---------|---------|
| `apps/web` | `@tendoriq/web` | Next.js 15 frontend |
| `apps/api` | `@tendoriq/api` | FastAPI backend (Python) |
| `packages/shared` | `@tendoriq/shared` | Shared TypeScript types, env schema, permissions |

`pnpm-workspace.yaml` includes `apps/*` and `packages/*`, so the API package participates in workspace installs (`workspace:*` deps).

## Requirements

- **Node** ≥ 20 (see `.nvmrc`)
- **pnpm** ≥ 9 (`packageManager` in root `package.json`)
- **Python** 3.12+ for API (`apps/api/requirements.txt`)

## Common commands

From the repo root:

```bash
pnpm install
pnpm dev                    # web + api via Turbo
pnpm dev:web                # @tendoriq/web only
pnpm dev:api                # @tendoriq/api only
pnpm build:web
pnpm --filter @tendoriq/web test -- --run
pnpm --filter @tendoriq/api run db:migrate
```

API Python (from `apps/api`):

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
# or: uv sync && uv run pytest tests/unit -q
```

## CI workflows

| Workflow | Role |
|----------|------|
| `ci.yml` | Lint, typecheck, API pytest, web Vitest, production build |
| `automated-tests.yml` | Extended suites, E2E (Playwright), scheduled runs |
| `production-ready.yml` | Template + build smoke checks (no live secrets required) |
| `deploy.yml` | Vercel frontend + Docker API image |

All Node jobs use **`pnpm install --frozen-lockfile`**, not `npm install`.

## Docker (API)

```bash
docker build -t tendoriq-api apps/api
docker run -p 8000:8000 -e DATABASE_URL=... tendoriq-api
```

Health check: `GET /health`.

## Frontend API client

Use **`@/lib/api-client`** for authenticated requests. `@/lib/api` re-exports the same client for legacy imports.
