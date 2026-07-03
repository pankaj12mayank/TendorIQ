# TenderIQ Lite

AI-assisted tender workflow: upload RFP documents, run structured analysis, draft proposals, and export results.

## Quick start

```bash
pnpm install   # One-time: install Node.js tools
pnpm setup     # One-time: create venv, install deps, create database
pnpm dev       # Start API (:8000) + Web (:3000)
```

Open **http://localhost:3000/sign-in**

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org) |
| pnpm | 9+ | `npm install -g pnpm` |

### First run

After `pnpm setup`, check `.tenderiq/owner-account.txt` for login credentials, or register at `/sign-up`.

### Stop

```bash
pnpm stop
```

Or press `Ctrl+C` in the terminal running `pnpm dev`.

## Commands

| Command | What it does |
|---------|-------------|
| `pnpm setup` | Create venv, install Python + Node deps, run migrations |
| `pnpm dev` | Start both servers (auto-runs setup if missing) |
| `pnpm dev:api` | Start API only |
| `pnpm dev:web` | Start Web only |
| `pnpm stop` | Kill all Python + Node processes |
| `pnpm migrate` | Run database migrations |
| `pnpm test:api` | Run API unit tests |

## Project structure

```
tenderiq/
├── api/           # FastAPI backend
├── web/           # Next.js frontend
├── scripts/       # Setup + dev runner (2 files)
├── docs/          # Documentation
├── .tenderiq/     # Runtime data (gitignored)
└── package.json   # Root commands
```

## Health

| URL | What |
|-----|------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/health | Liveness |
| http://localhost:8000/health/ready | Readiness |

## Troubleshooting

**Login fails / DB schema out of date:**
```bash
pnpm stop
pnpm migrate
pnpm dev
```

**Port in use:**
```bash
pnpm stop
```

**Reset everything:**
```bash
pnpm stop
rmdir /s /q api\venv
del .tenderiq\data\tenderiq.db
pnpm setup
```
