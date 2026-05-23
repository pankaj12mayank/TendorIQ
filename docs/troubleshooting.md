# Troubleshooting Guide

> **Local dev:** MySQL + `run.bat` / `run.bat check` — not PostgreSQL or Redis. See [MYSQL_SETUP.md](./MYSQL_SETUP.md).

## Local quick checks

```batch
run.bat check
```

Fails on MySQL → start MySQL service, fix `DATABASE_URL` in `.env`.  
Fails on migrations → `cd apps\api` then `python -m alembic upgrade head` with `DOTENV_PATH=../../.env`.

---

## Common Issues

### API Issues

#### 401 Unauthorized

**Symptoms:** API returns 401 error

**Causes:**
1. Missing or expired JWT token
2. Invalid token format
3. Clerk configuration issue

**Solutions:**
```bash
# 1. Check token is present
curl -H "Authorization: Bearer <token>" ...

# 2. Verify token hasn't expired
# JWT expiry is typically 1 hour

# 3. Check Clerk keys
echo $CLERK_SECRET_KEY
# Should start with sk_test_ or sk_live_
```

---

#### 500 Internal Server Error

**Symptoms:** API returns 500

**Diagnosis:**
```bash
# Check Sentry for error details
# Or check logs:
railway logs
docker logs tenderiq-api
```

**Common Causes:**
- MySQL connection failed (`DATABASE_URL` wrong or service stopped)
- Unhandled exception in code
- Optional: Redis only if you enabled distributed rate limiting

**Solutions:**
```python
# Add try-catch to identify issue
try:
    result = await db.query(...)
except Exception as e:
    logger.error(f"DB error: {e}")
    raise
```

---

#### 422 Validation Error

**Symptoms:** `detail: "Input should be..."`

**Causes:**
- Invalid data format
- Missing required fields
- Type mismatch

**Solution:**
```bash
# Check request body matches schema
# Example: tender creation
{
  "title": "string",      # Required
  "deadline": "2026-01-01T00:00:00Z",  # ISO format
  "budget": 100000         # Number, not string
}
```

---

### Database Issues

#### Connection Refused

**Error:** `Can't connect to MySQL server` / connection refused

**Solutions:**
```bash
# 1. Check DATABASE_URL (MySQL only)
# mysql+aiomysql://user:pass@localhost:3306/tenderiq?charset=utf8mb4

# 2. Verify database exists
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS tenderiq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 3. Windows: start MySQL80 service; Linux: systemctl start mysql
```

---

#### Query Timeout

**Error:** `canceling statement due to timeout`

**Solutions:**
```sql
-- Add indexes
CREATE INDEX idx_tender_tenant ON tenders(tenant_id);
CREATE INDEX idx_document_tender ON documents(tender_id);

-- Optimize query
EXPLAIN ANALYZE SELECT * FROM tenders WHERE ...
```

---

### Queue & background jobs

TenderIQ uses **inline** `email_process` jobs in the API process (no ARQ worker). Platform queue UI: **Admin → Queue** (`/dashboard/admin?module=queue`).

#### Jobs Not Processing

**Symptoms:** Email stuck pending, OCR not advancing

**Solutions:**
```bash
# 1. API must be running (run.bat or uvicorn)
curl http://localhost:8000/health

# 2. Super admin: retry from Admin → Queue or Failed Jobs
# POST /api/v1/admin/platform/queue/jobs/{id}/retry

# 3. Email queue: Admin → Email System → Queue tab → Retry
```

Optional **Redis** is not required for the default queue; only for experimental distributed rate limits.

---

#### Dead Letter Queue Building Up

**Solutions:**
```bash
# 1. View dead letter jobs
curl https://api.tenderiq.com/queue/dead-letter

# 2. Retry individual job
curl -X POST https://api.tenderiq.com/queue/dead-letter/{job_id}/retry

# 3. Retry all for queue
curl -X POST "https://api.tenderiq.com/queue/dead-letter/retry-all?queue=ocr"
```

---

### Frontend Issues

#### White Screen on Load

**Diagnosis:**
1. Check browser console for errors
2. Check network tab for failed requests

**Common Causes:**
- API not running
- CORS blocking
- Invalid environment variables

**Solutions:**
```bash
# 1. Start API
cd apps/api
uv run uvicorn main:app --reload

# 2. Check CORS config
# Should include your frontend URL

# 3. Verify env vars
# In .env.local:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

#### Upload Not Working

**Symptoms:** Upload shows "Failed" or hangs

**Solutions:**
```bash
# 1. Check file size limit (default 50MB)
# Check server logs for size errors

# 2. Check S3/storage configuration
# Verify credentials in environment

# 3. Check network
# Try smaller file first
```

---

#### Authentication Redirect Loop

**Symptoms:** Continuously redirected to login

**Solutions:**
```bash
# 1. Check Clerk configuration
# Verify CLERK_PUBLISHABLE_KEY is correct

# 2. Check JWT validation
# Verify CLERK_SECRET_KEY matches

# 3. Clear browser storage
# Clear cookies and localStorage
```

---

### AI Issues

#### API Key Errors

**Error:** `Invalid API key` or `Authentication error`

**Solutions:**
```bash
# 1. Verify key is set
echo $OPENAI_API_KEY
# Should start with sk-

# 2. Check key has credits
# Go to OpenAI dashboard

# 3. Check quota
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/usage
```

---

#### Rate Limit Errors

**Error:** `Rate limit exceeded`

**Solutions:**
```python
# Implement retry with backoff
for attempt in range(3):
    try:
        result = await call_api()
    except RateLimitError:
        await asyncio.sleep(2 ** attempt)
```

---

#### Model Not Available

**Error:** `Model not found`

**Solutions:**
```bash
# 1. Check model name
# Use: gpt-4, gpt-3.5-turbo, claude-3-sonnet

# 2. Check provider status
# Check OpenAI/Anthropic status pages

# 3. Check region availability
# Some models only available in certain regions
```

---

### Performance Issues

#### Slow API Response

**Diagnosis:**
```bash
# Check response time
time curl -w "\nTime: %{time_total}s\n" https://api.tenderiq.com/tenders
```

**Solutions:**
1. Add indexes to frequently queried columns
2. Implement caching with Redis
3. Add pagination to list endpoints
4. Check for N+1 queries

---

#### High Memory Usage

**Diagnosis:**
```bash
# Check API container memory
docker stats tenderiq-api
```

**Solutions:**
1. Set query limits
2. Implement pagination
3. Add connection pooling
4. Optimize JSON serialization

---

## Debug Commands

### API Diagnostics

```bash
# Health check
curl https://api.tenderiq.com/health

# Readiness check
curl https://api.tenderiq.com/health/ready

# Metrics
curl https://api.tenderiq.com/observability/metrics/summary

# Queue stats
curl https://api.tenderiq.com/queue/stats
```

### Database Diagnostics

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check slow queries
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

---

## Getting Help

If these solutions don't work:

1. **Check docs**: [docs.tenderiq.com](https://docs.tenderiq.com)
2. **Search issues**: [github.com/tenderiq/tenderiq/issues](https://github.com/tenderiq/tenderiq/issues)
3. **Ask community**: [Discord](https://discord.gg/tenderiq)
4. **Contact support**: support@tenderiq.com

When contacting support, include:
- Error message
- Steps to reproduce
- Environment details
- Relevant logs