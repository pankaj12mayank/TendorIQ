# TenderIQ - Tender Management Platform

A production-grade monorepo for building a tender management platform with Next.js, FastAPI, PostgreSQL, and Redis.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15 (App Router) + TypeScript |
| **Backend** | FastAPI + Python 3.12 |
| **Database** | PostgreSQL (async via SQLAlchemy + asyncpg) |
| **Queue** | ARQ + Redis |
| **Auth** | Clerk (frontend) |
| **Styling** | Tailwind CSS + shadcn/ui |
| **Monorepo** | pnpm workspaces + Turborepo |

## Architecture

```
tendoriq/
├── apps/
│   ├── web/          # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/           # App Router pages
│   │   │   ├── components/    # React components
│   │   │   ├── lib/           # Utilities (api, utils)
│   │   │   └── types/         # TypeScript types
│   │   └── ...
│   │
│   └── api/          # FastAPI backend
│       ├── src/
│       │   ├── api/          # API routes
│       │   ├── core/         # Core modules (config, db, redis)
│       │   └── models/       # SQLAlchemy models
│       └── ...
│
├── packages/
│   └── shared/       # Shared code between apps
│       ├── src/
│       │   ├── env.ts        # Environment validation
│       │   ├── constants/    # App constants
│       │   └── types/        # Zod schemas & TypeScript types
│       └── package.json
│
├── scripts/          # Development scripts
├── .github/         # CI/CD workflows
└── docker-compose.yml  # Optional Docker setup
```

## Quick Start

### Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.12+
- uv (Python package manager)
- PostgreSQL 16+
- Redis 7+

### Installation

```bash
# Clone and navigate to project
cd tendoriq

# Install dependencies
pnpm install

# Copy environment file
cp .env.example .env

# Update .env with your credentials
# (especially DATABASE_URL, REDIS settings, and auth keys)
```

### Running Locally

```bash
# Start all services (frontend + backend)
pnpm dev

# Or start individually:
pnpm dev:web    # Frontend on http://localhost:3000
pnpm dev:api    # Backend on http://localhost:8000

# View API docs: http://localhost:8000/docs
```

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start all apps in development |
| `pnpm build` | Build all apps |
| `pnpm lint` | Lint all apps |
| `pnpm typecheck` | TypeScript type checking |
| `pnpm format` | Format code with Prettier |

## Environment Variables

See `.env.example` for all available variables. Key ones:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_HOST/PORT` - Redis connection
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` - Clerk auth
- `JWT_SECRET` - Auth token secret

## Deployment

### Frontend (Vercel)

1. Push to GitHub
2. Import project in Vercel
3. Set environment variables
4. Deploy automatically

### Backend (Railway)

1. Push to GitHub
2. Create Railway project
3. Link to repository
4. Set environment variables
5. Deploy from Dockerfile or build command

## Development Guidelines

### Code Style

- ESLint + Prettier for TypeScript
- Ruff for Python
- Follow existing patterns in codebase

### Adding Features

1. Add shared types to `packages/shared`
2. Create API routes in `apps/api/src/api/`
3. Create pages in `apps/web/src/app/`
4. Use shared constants and types

### Database

- Models in `apps/api/src/models/`
- Migrations with Alembic
- Schema validation via Zod

## License

MIT