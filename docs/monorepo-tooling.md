# Monorepo & tooling

TenderIQ is a **pnpm + Turbo** monorepo. The API is Python; Node packages exist so Turbo can orchestrate `dev` / `lint` / `test` scripts.

## Layout

| Path | Package | Purpose |
|------|---------|---------|
| `apps/web` | `@tendoriq/web` | Next.js 15 frontend |
| `apps/api` | `@tendoriq/api` | FastAPI backend (Python) |
| `packages/shared` | `@tendoriq/shared` | Shared TypeScript types, env schema, permissions |

`pnpm-workspace.yaml` includes `apps/*` and `packages/*`.

## Requirements (aligned)

| Tool | Version | Notes |
|------|---------|--------|
| **Node** | ≥ 20 | `.nvmrc`, `package.json` engines |
| **pnpm** | ≥ 9 | `packageManager` in root `package.json` |
| **Python** | 3.12+ | root `pyproject.toml`, API runtime |

## Python dependencies (single graph)

| File | Use |
|------|-----|
| `apps/api/requirements.txt` | Production runtime (Railway / Porter pip) |
| `apps/api/requirements-dev.txt` | Local `venv`, `run.bat`, **CI** (includes `-r requirements.txt` + pytest, ruff, mypy) |

**Local (Windows):** `run.bat` / `run.bat setup` → `scripts/tenderiq-start.ps1` → `pip install -r requirements-dev.txt` into `apps/api/venv`.

**CI:** `.github/actions/setup-api-python` creates the same venv and installs `requirements-dev.txt`.

**Optional:** `pnpm install` runs `scripts/postinstall.js` to refresh an existing venv; full setup still uses `run.bat`.

Root `pyproject.toml` holds **tool config** (ruff, mypy, pytest paths). Do not use `uv sync` from `apps/api` alone — there is no `pyproject.toml` under `apps/api`.

## Node install policy

- **CI / normal start:** `pnpm install --frozen-lockfile`
- **`run.bat setup`:** may update the lockfile (no `--frozen-lockfile`)

## Common commands

From repo root:

```bash
pnpm install
pnpm dev                    # Turbo: web + api package scripts
pnpm dev:web
pnpm dev:api
pnpm build:web
pnpm --filter @tendoriq/web test -- --run
```

**Windows one-click (no Turbo):** `run.bat` starts uvicorn + `pnpm --filter @tendoriq/web dev` directly for reliable hidden windows. For Turbo graph dev, use `run.bat dev` or `pnpm dev`.

API Python (from `apps/api` after venv exists):

```bash
# Windows
venv\Scripts\python.exe -m pytest tests/unit -q

# Linux/macOS
./venv/bin/python -m pytest tests/unit -q
```

## CI workflows (no drift)

All workflows share:

- Node **20**, pnpm **9**, `pnpm install --frozen-lockfile`
- Python **3.12**, `.github/actions/setup-api-python` → `requirements-dev.txt`

| Workflow | Role |
|----------|------|
| `ci.yml` | Lint, typecheck, API pytest, web Vitest, production build |
| `automated-tests.yml` | Extended suites, E2E (Playwright), scheduled runs |
| `production-ready.yml` | Template + build smoke checks (no live secrets required) |
| `deploy.yml` | Vercel frontend + Railway API (Nixpacks) |

When changing Python or Node versions, update **`.github/actions/setup-api-python`**, root `package.json` engines, and this doc together.

## API deploy (no Docker)

Production API: **`apps/api/railway.json`** (Nixpacks) or equivalent on Porter/Render — `pip install -r requirements.txt`, then `uvicorn src.main:app`.

See `docs/deployment.md`.

## Frontend API client

Use **`@/lib/api-client`** for authenticated requests. `@/lib/api` re-exports the same client for legacy imports.
