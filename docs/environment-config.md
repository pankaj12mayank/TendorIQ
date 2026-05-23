# TenderIQ Environment Configuration Guide

> **Required for local dev:** `DATABASE_URL` (MySQL) — see [MYSQL_SETUP.md](./MYSQL_SETUP.md) **before** filling optional keys below.  
> **Redis** is optional (rate limiting only); queues run in-process.

## Overview

TenderIQ uses centralized environment configuration management with:
- Schema-based validation (Zod for frontend, Pydantic for backend)
- Type-safe environment access
- Platform detection (Railway, Vercel, local)
- Feature flags for gradual rollouts

## Environment Files

```
.env                 # Development (git-ignored)
.env.staging        # Staging (git-ignored)
.env.production     # Production (git-ignored)
.env.example        # Template (committed)
```

## Loading Priority

### Development
1. `.env.local` (highest priority)
2. `.env`

### Production (Railway/Vercel)
1. Environment variables set in dashboard
2. `.env` as fallback

## Platform Detection

```typescript
import { isRailway, isVercel, getAppUrl, getApiUrl } from '@tendoriq/shared';

console.log(isRailway); // true on Railway
console.log(isVercel);  // true on Vercel

const appUrl = getAppUrl(); // Auto-detects platform URL
```

## Railway Configuration

### Required Environment Variables

```bash
# Set on Railway (use MySQL plugin or external MySQL)
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/tenderiq?charset=utf8mb4
# REDIS_URL=redis://...   # optional — not required for email/OCR queue
RAILWAY_SERVICE_NAME=tendoriq-api
RAILWAY_PUBLIC_DOMAIN=tendoriq-api.up.railway.app

# Must be set in Railway dashboard
JWT_SECRET=<min-32-chars>
CLERK_SECRET_KEY=sk_...
SENTRY_DSN=https://...
OPENAI_API_KEY=sk-...
RESEND_API_KEY=re_...
```

### Railway Deployment

1. Connect GitHub repository
2. Add environment variables in Railway dashboard
3. Deploy with `railway up`
4. Configure custom domain if needed

## Vercel Configuration

### Required Environment Variables

```bash
# Auto-provisioned by Vercel
VERCEL=true
VERCEL_ENV=production
VERCEL_GIT_COMMIT_REF=main
VERCEL_GIT_COMMIT_SHA=abc123

# Must be set in Vercel dashboard
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
# DATABASE_URL on API host only (mysql+aiomysql://...)
NEXT_PUBLIC_API_URL=https://api.tendoriq.com
```

### Vercel Deployment

1. Import GitHub repository
2. Add environment variables in Vercel dashboard
3. Deploy automatically on push

## Secret Handling Strategy

### Development
- Use `.env` file (git-ignored)
- Never commit secrets

### Production

**Option 1: Platform Secrets**
- Railway: Set in dashboard
- Vercel: Set in dashboard

**Option 2: Secrets Manager**
```bash
# Example: Fetch from HashiCorp Vault
export JWT_SECRET=$(vault read -field=value secret/tendoriq/jwt-secret)
export DATABASE_URL=$(vault read -field=value secret/tendoriq/database)
```

**Option 3: CI/CD Injected**
```yaml
# GitHub Actions
- name: Set production secrets
  run: |
    echo "$JWT_SECRET" | gh secret set JWT_SECRET --repo owner/tendoriq
```

## Environment Validation

### Frontend (TypeScript)

```typescript
import { env, isProd, features } from '@tendoriq/shared';

// Access validated env vars
const apiUrl = env.NEXT_PUBLIC_API_URL;

// Check environment
if (isProd) {
  // Production-specific logic
}

// Use feature flags
if (features.aiAnalysis) {
  // AI features enabled
}
```

### Backend (Python)

```python
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

# Access validated settings
database_url = settings.DATABASE_URL

# Production checks
if settings.is_production:
    logger.info("Production mode enabled")

# Feature flags
if settings.FEATURE_AI_ANALYSIS:
    logger.info("AI features enabled")
```

## Feature Flags

```typescript
import { isFeatureAvailable } from '@tendoriq/shared/config/feature-flags';

if (isFeatureAvailable('ai_analysis')) {
  // Show AI features to user
}
```

### Available Flags

| Flag | Description | Default |
|------|-------------|---------|
| `ai_analysis` | AI-powered tender analysis | true |
| `document_ocr` | OCR for documents | false |
| `advanced_analytics` | Advanced reporting | false |
| `webhooks` | Webhook notifications | true |
| `api_access` | REST API access | true |
| `custom_domains` | Custom domain support | false |
| `sso` | Single sign-on | false |

## Redis Configuration (optional)

Not required for local dev or default deploy (`run.bat`, inline email/OCR). Use only if enabling Redis-backed rate limiting.

### Local Development
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Production (Railway)
```
REDIS_URL=redis://username:password@host:port/db
```

### Production (Upstash)
```
REDIS_URL=redis://default:xxxx@upstash.io:6379
```

## R2/S3 Configuration

### Cloudflare R2 (Recommended)
```
STORAGE_PROVIDER=r2
AWS_REGION=auto
AWS_S3_BUCKET=tendoriq-prod
AWS_ACCESS_KEY_ID=<r2-access-key>
AWS_SECRET_ACCESS_KEY=<r2-secret-key>
AWS_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
```

### AWS S3
```
STORAGE_PROVIDER=s3
AWS_REGION=us-east-1
AWS_S3_BUCKET=tendoriq-prod
AWS_ACCESS_KEY_ID=<aws-access-key>
AWS_SECRET_ACCESS_KEY=<aws-secret-key>
```

## AI Provider Configuration

### OpenAI
```
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_MODEL=gpt-4
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.7
```

### Anthropic
```
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-...
AI_MODEL=claude-3-opus-20240229
```

### Azure OpenAI
```
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

## Security Checklist

- [ ] JWT_SECRET is minimum 32 characters
- [ ] DATABASE_URL uses SSL in production
- [ ] REDIS_URL uses TLS in production (if Redis is used)
- [ ] CORS_ORIGINS restricts to known domains
- [ ] INTERNAL_API_KEY set for service-to-service auth
- [ ] SENTRY_DSN set for error tracking
- [ ] Feature flags reviewed for production
- [ ] Environment files git-ignored
- [ ] No secrets in code commits
- [ ] Secrets rotated regularly

## Troubleshooting

### "Missing critical environment variables"
- Check JWT_SECRET is set
- Check DATABASE_URL is set

### "Invalid environment configuration"
- Run validation: `pnpm typecheck`
- Check .env file format

### Platform detection issues
- Verify RAILWAY_SERVICE_NAME or VERCEL env vars
- Check platform docs for latest env var names