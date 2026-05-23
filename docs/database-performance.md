# TenderIQ Database Performance Optimization Guide

> **Database:** MySQL 8+ in production. PostgreSQL / `postgresql.conf` sections are legacy reference only.

## Index Strategy

### High-Frequency Query Indexes
```sql
-- Tenant isolation (always filter by tenant)
CREATE INDEX idx_tenders_tenant_id ON tenders(tenant_id);
CREATE INDEX idx_documents_tenant_id ON documents(tenant_id);
CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);

-- Status-based filtering
CREATE INDEX idx_tenders_status ON tenders(status);
CREATE INDEX idx_bids_status ON bids(status);
CREATE INDEX idx_notifications_read ON notifications(is_read);

-- Date-based queries
CREATE INDEX idx_tenders_closing_date ON tenders(closing_date);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_usage_logs_created ON usage_logs(created_at DESC);

-- User activity
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_usage_logs_user ON usage_logs(user_id, created_at DESC);
```

### Composite Indexes
```sql
-- Multi-tenant filtering with status
CREATE INDEX idx_tender_tenant_status ON tenders(tenant_id, status);
CREATE INDEX idx_bid_tender_status ON bids(tender_id, status);

-- Tenant with date range
CREATE INDEX idx_audit_tenant_date ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_usage_tenant_date ON usage_logs(tenant_id, created_at DESC);
```

## Partitioning Strategy

### Time-Based Partitioning for Large Tables
```sql
-- Partition usage_logs by month
CREATE TABLE usage_logs (
    LIKE usage_logs INCLUDING ALL
) PARTITION BY RANGE (created_at);

CREATE TABLE usage_logs_2024_01 PARTITION OF usage_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Partition audit_logs by month
CREATE TABLE audit_logs PARTITION BY RANGE (created_at);
```

### List Partitioning for Status
```sql
-- Partition queue_jobs by status
CREATE TABLE queue_jobs (
    LIKE queue_jobs INCLUDING ALL
) PARTITION BY LIST (status);

CREATE TABLE queue_jobs_pending PARTITION OF queue_jobs
    FOR VALUES IN ('pending');
CREATE TABLE queue_jobs_completed PARTITION OF queue_jobs
    FOR VALUES IN ('completed', 'failed');
```

## Query Optimization

### Pagination
```python
# Use keyset pagination for large datasets
# Instead of: OFFSET 10000 LIMIT 20
# Use: WHERE id < last_seen_id LIMIT 20

async def get_tenders(cursor: Optional[str] = None, limit: int = 20):
    query = select(Tender).order_by(Tender.created_at.desc())
    if cursor:
        cursor_date = datetime.fromisoformat(cursor)
        query = query.where(Tender.created_at < cursor_date)
    return await session.execute(query.limit(limit))
```

### Eager Loading
```python
# Avoid N+1 queries with joinedload
from sqlalchemy.orm import joinedload

async def get_tenders_with_relations(tenant_id: str):
    return await session.execute(
        select(Tender)
        .options(joinedload(Tender.documents))
        .options(joinedload(Tender.checklists))
        .where(Tender.tenant_id == tenant_id)
    )
```

### Tenant Isolation
```python
# Always filter by tenant_id
class TenderRepository:
    async def get_all(self, tenant_id: str, **kwargs):
        kwargs['filters'] = {**kwargs.get('filters', {}), 'tenant_id': tenant_id}
        return await super().get_all(**kwargs)
```

## Caching Strategy

> **Optional:** Redis examples below are not required for the default MySQL + `run.bat` stack.

### Redis Caching (optional)
```python
async def get_cached_tender(tender_id: str, tenant_id: str):
    key = f'tender:{tenant_id}:{tender_id}'
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)

    tender = await db.get(Tender, tender_id)
    if tender and tender.tenant_id == tenant_id:
        await redis.setex(key, 300, json.dumps(tender))
    return tender
```

### Cache Invalidation
```python
async def invalidate_tender_cache(tender_id: str, tenant_id: str):
    pattern = f'tender:{tenant_id}:*'
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)
```

## Monitoring & Metrics

### Slow Query Detection
```sql
-- Enable query timing
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Query statistics
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 20;
```

### Table Statistics
```sql
-- Analyze tables regularly
ANALYZE tenders;
ANALYZE bids;
ANALYZE documents;

-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

## Connection Pooling

### Optimal Pool Settings
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Maintain 20 connections
    max_overflow=10,       # Allow 10 overflow connections
    pool_pre_ping=True,    # Test connections before use
    pool_recycle=3600,     # Recycle connections every hour
)
```

## Recommended Configuration

### MySQL 8 (primary)

See [MYSQL_SETUP.md](./MYSQL_SETUP.md). Typical tuning: `innodb_buffer_pool_size`, slow query log, indexes on `tenant_id` foreign keys.

### PostgreSQL Settings (legacy reference only)
```ini
# postgresql.conf — not used by TenderIQ default deploy
shared_buffers = 256MB          # 25% of RAM
effective_cache_size = 768MB    # 75% of RAM
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB

# Enable query planning optimization
shared_preload_libraries = 'pg_stat_statements'
```

### Connection Limits
```sql
-- Set max connections based on expected concurrent users
ALTER SYSTEM SET max_connections = 200;
```

## Maintenance Tasks

### Vacuum & Analyze
```sql
-- Schedule regular maintenance
VACUUM ANALYZE tenders;
VACUUM ANALYZE bids;
VACUUM ANALYZE usage_logs;
```

### Index Maintenance
```sql
-- Reindex for performance
REINDEX INDEX CONCURRENTLY idx_tender_tenant_status;
```

### Data Archival
```sql
-- Archive old data to separate tables
CREATE TABLE audit_logs_archive (LIKE audit_logs);
INSERT INTO audit_logs_archive SELECT * FROM audit_logs WHERE created_at < NOW() - INTERVAL '1 year';
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '1 year';
```