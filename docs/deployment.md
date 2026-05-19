# Deployment Guide

## Overview

This guide covers deploying TenderIQ to production environments.

---

## Prerequisites

- [ ] PostgreSQL 15+ database (Neon, Supabase, or self-hosted)
- [ ] Redis 7+ (Redis Cloud or self-hosted)
- [ ] Domain configured with SSL
- [ ] Sentry project created for error tracking

---

## Environment Setup

### 1. Create Environment File

```bash
# Production environment variables
DATABASE_URL=postgresql://user:pass@host:5432/tenderiq
REDIS_URL=redis://:password@host:6379/0

# Auth (Clerk)
CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# AI Providers
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Security
SECRET_KEY=<generate-32-char-random-string>

# Sentry
SENTRY_DSN=https://xxx@sentry.io/xxx

# Production URLs
APP_URL=https://tenderiq.com
API_URL=https://api.tenderiq.com

# CORS
CORS_ORIGINS=https://tenderiq.com
```

### 2. Generate Secret Key

```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Deployment Options

### Option 1: Railway (Recommended)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize
railway init tenderiq

# Add variables
railway variables set DATABASE_URL=...

# Deploy
railway up
```

**Railway Configuration (railway.json):**
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd apps/api && uv sync && cd ../web && pnpm install && pnpm build"
  },
  "run": {
    "command": "cd apps/api && uv run uvicorn main:app --host 0.0.0.0 --port $PORT",
    "web": true
  }
}
```

### Option 2: Docker

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Install dependencies
COPY apps/api/pyproject.toml .
RUN uv sync --no-dev

# Copy source
COPY apps/api/src ./src

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build & Run:**
```bash
docker build -t tenderiq-api .
docker run -d -p 8000:8000 --env-file .env.production tenderiq-api
```

### Option 3: Vercel + Neon

1. Connect GitHub to Vercel
2. Add environment variables
3. Deploy with `pnpm vercel:deploy`

---

## Database Setup

### 1. Run Migrations

```bash
cd apps/api
uv run alembic upgrade head
```

### 2. Seed Initial Data

```bash
uv run python -m scripts.seed_db
```

---

## Frontend Deployment

### Vercel (Recommended)

```bash
cd apps/web
npx vercel --prod
```

### Netlify

```bash
cd apps/web
netlify deploy --prod --dir=.next
```

---

## SSL & Domain

### Using Cloudflare

1. Add domain to Cloudflare
2. Create CNAME record pointing to deployment
3. Enable "Full" SSL mode
4. Enable "Always Use HTTPS"

---

## Post-Deployment Checklist

- [ ] Health endpoint returns 200
- [ ] Database connection working
- [ ] Redis connection working
- [ ] Authentication working
- [ ] File uploads working
- [ ] AI features working
- [ ] Sentry receiving errors
- [ ] Metrics visible

---

## Monitoring

### Health Checks

```bash
# Basic
curl https://api.tenderiq.com/health

# Readiness (includes DB + Redis)
curl https://api.tenderiq.com/health/ready
```

### Logs

```bash
# Railway
railway logs

# Docker
docker logs tenderiq-api

# CloudWatch (if using AWS)
aws logs tail /aws/lambda/tenderiq
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

1. Use Redis for session storage (already configured)
2. Use database-backed job queue (ARQ)
3. Enable sticky sessions or move to stateless

### Database Scaling

- **Read Replicas**: For heavy read loads
- **Connection Pooling**: Use PgBouncer
- **Caching**: Add Redis cache layer

---

## Rollback

### Railway

```bash
railway rollback
```

### Docker

```bash
docker pull tenderiq-api:previous-tag
docker-compose up -d
```

---

## Security Hardening

1. **Firewall**: Only allow ports 80, 443
2. **Rate Limiting**: Already enabled
3. **CORS**: Restrict to production domain
4. **Headers**: Security headers via middleware
5. **Secrets**: Rotate regularly

---

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL
pg_dump $DATABASE_URL > backup.sql

# Schedule daily backups via cron
0 2 * * * pg_dump $DATABASE_URL > /backups/tenderiq-$(date +\%Y\%m\%d).sql
```

### Restore

```bash
psql $DATABASE_URL < backup.sql
```

---

## Troubleshooting

See [Troubleshooting Guide](docs/troubleshooting.md) for common issues.