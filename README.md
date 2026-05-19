# TenderIQ - AI-Powered Tender Management Platform

<p align="center">
  <img src="apps/web/public/logo.svg" alt="TenderIQ" width="200"/>
</p>

<p align="center">
  <a href="https://tenderiq.com">Website</a> •
  <a href="https://docs.tenderiq.com">Documentation</a> •
  <a href="https://discord.gg/tenderiq">Community</a>
</p>

---

## What is TenderIQ?

TenderIQ is an enterprise-grade SaaS platform for managing tender documents, bids, and proposals with AI-powered analysis and extraction.

### Key Features

- 📄 **Document Management** - Upload, organize, and version tender documents
- 🔍 **AI Extraction** - Extract structured data using LLMs (OpenAI, Anthropic, Azure)
- 📊 **Analytics** - Real-time dashboards and usage metrics
- 🔐 **Enterprise Security** - RBAC, tenant isolation, audit logging
- 🚀 **Async Processing** - Queue-based OCR, parsing, and analysis
- 📦 **Export** - Generate reports in PDF, Excel, Word formats

---

## Tech Stack

| Layer | Technology |
|-------|-------------|
| Frontend | React 18, Next.js 14, TypeScript, Tailwind |
| Backend | FastAPI, Python 3.12, Pydantic |
| Database | PostgreSQL 15 (Neon, Supabase) |
| Queue | Redis 7 + ARQ |
| Auth | Clerk + JWT |
| AI | OpenAI, Anthropic, Azure OpenAI, Ollama |
| Monitoring | Sentry, Custom Metrics |
| Deploy | Railway, Vercel, Docker |

---

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- pnpm 9+

### Setup

```bash
# Clone repository
git clone https://github.com/yourorg/tenderiq.git
cd tenderiq

# Install dependencies
pnpm install

# Setup environment
cp .env.example .env

# Start development
pnpm dev
```

### Environment Variables

See [Environment Configuration](docs/environment-config.md) for details.

---

## Project Structure

```
tenderiq/
├── apps/
│   ├── api/           # FastAPI backend
│   │   └── src/
│   │       ├── api/       # Routes, schemas, dependencies
│   │       ├── core/      # Models, services, utilities
│   │       └── main.py    # Entry point
│   └── web/           # Next.js frontend
│       └── src/
│           ├── app/           # App router pages
│           ├── components/   # React components
│           ├── hooks/        # Custom hooks
│           └── lib/          # Utilities
├── packages/
│   └── shared/        # Shared code (types, utils)
├── docs/             # Documentation
├── .github/          # GitHub Actions
└── scripts/          # Dev scripts
```

---

## Development

### Commands

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start all apps in dev mode |
| `pnpm dev:api` | Backend only |
| `pnpm dev:web` | Frontend only |
| `pnpm build` | Build all apps |
| `pnpm lint` | Lint all code |
| `pnpm typecheck` | Type check all code |
| `pnpm test` | Run tests |

### Code Style

- **Python**: ruff + mypy
- **TypeScript**: ESLint + Prettier

---

## API Reference

See [API Documentation](docs/api-docs.md) for full endpoint reference.

### Base URL

```
Production: https://api.tenderiq.com/v1
Staging:    https://api-staging.tenderiq.com/v1
Local:      http://localhost:8000/v1
```

### Authentication

```bash
curl -H "Authorization: Bearer <JWT>" https://api.tenderiq.com/v1/tenders
```

---

## Deployment

See [Deployment Guide](docs/deployment.md) for production deployment.

### Quick Deploy

```bash
# Railway (recommended)
pnpm railway:deploy

# Docker
docker build -t tenderiq .
docker run tenderiq
```

---

## Monitoring

- **Health**: `GET /health`
- **Ready**: `GET /health/ready`
- **Metrics**: `GET /observability/metrics/summary`
- **Sentry**: Configure DSN in environment

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

---

## Support

- 📧 Email: support@tenderiq.com
- 💬 Discord: [Join Community](https://discord.gg/tenderiq)
- 📖 [Documentation](https://docs.tenderiq.com)

---

## License

MIT License - see [LICENSE](LICENSE) for details.