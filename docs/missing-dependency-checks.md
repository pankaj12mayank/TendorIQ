# Missing Dependency Checks

## Production Readiness

### Required Dependencies

| Dependency | Purpose | Status | Action |
|------------|---------|--------|--------|
| sentry-sdk | Error tracking | ✅ Configured | None |
| pytest | Testing | ✅ Installed | None |
| mypy | Type checking | ✅ Configured | None |
| ruff | Linting | ✅ Configalled | None |

### Missing Production Dependencies

| Dependency | Priority | Purpose | Recommendation |
|------------|----------|---------|----------------|
| sentry-sdk[fastapi] | High | FastAPI integration | Install `sentry-sdk[fastapi]` |
| pytest-cov | Medium | Coverage reports | Add to dev deps |
| pytest-asyncio | High | Async tests | Add to test deps |
| httpx | High | Test client | Add to test deps |

### Install Missing

```bash
# API
cd apps/api
uv add --dev pytest-cov pytest-asyncio httpx

# Verify sentry integrations
pip install sentry-sdk[fastapi] sentry-sdk[redis] sentry-sdk[sqlalchemy]
```

---

## Frontend Dependencies

| Dependency | Purpose | Status | Action |
|------------|---------|--------|--------|
| @tanstack/react-query | Data fetching | ✅ Installed | None |
| @tanstack/react-table | Tables | ✅ Installed | None |
| react-hook-form | Forms | ✅ Installed | None |
| zod | Validation | ✅ Installed | None |
| @sentry/react | Error tracking | ⚠️ Missing | Add @sentry/react |
| @tanstack/react-virtual | Virtual scrolling | ⚠️ Missing | Add for large lists |

### Install

```bash
cd apps/web
pnpm add @sentry/react @tanstack/react-virtual
```

---

## Infrastructure Dependencies

| Service | Status | Notes |
|---------|--------|-------|
| PostgreSQL 15+ | ✅ Configured | Multi-tenant ready |
| Redis 7+ | ✅ Configured | Queue + cache |
| S3/Blob Storage | ⚠️ Config | Verify credentials |
| Stripe | ⚠️ Webhook | Verify endpoint |

---

## Missing Feature Checks

### 1. Payment Processing
- [ ] Stripe integration complete
- [ ] Webhook handler tested
- [ ] Plan limits enforced
- [ ] Usage tracking implemented

### 2. Error Tracking
- [ ] Sentry initialized on startup
- [ ] Error boundaries in React
- [ ] Custom error categories

### 3. Monitoring
- [ ] Health checks verified
- [ ] Metrics endpoint working
- [ ] Alerting configured

### 4. Security
- [ ] Secrets rotated
- [ ] API keys different from dev
- [ ] CORS configured for production

---

## Checklist

```bash
# Before deployment, verify:

# Python deps (same as run.bat / CI)
cd apps/api
pip install -r requirements-dev.txt
python -c "import sentry_sdk; print('Sentry OK')"
python -c "import pytest; print('Pytest OK')"

# Node deps
cd apps/web
pnpm install
pnpm audit --audit-level=high

# Infrastructure
curl -f http://localhost:8000/health || exit 1
```

---

## Security Checklist

- [ ] No hardcoded secrets in code
- [ ] Environment variables used for all secrets
- [ ] Database credentials rotated
- [ ] Redis password set
- [ ] API keys are production values (not test)
- [ ] Sentry DSN is production project
- [ ] CORS restricted to production domain

---

## Dependencies to Remove (bloated)

| Package | Reason |
|---------|--------|
| @types/node | Redundant with TS 5+ |
| @types/react | Redundant with react 18+ types |
| some-unused-ui-lib | Check package.json |

Run: `pnpm dedupe`