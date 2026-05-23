# Scaling Strategy

> **As deployed today:** MySQL 8+, FastAPI with **in-process** background jobs (`core.tasks.inline`). Redis/PostgreSQL sections below are **roadmap / optional** unless noted.

## Overview

This document outlines scaling from startup to enterprise. Align production setup with [deployment.md](deployment.md) and [MYSQL_SETUP.md](MYSQL_SETUP.md).

---

## Current Architecture

- **API**: FastAPI (single or horizontally scaled instances)
- **Database**: MySQL 8+
- **Queue / email**: DB tables + inline workers (no Redis required)
- **Frontend**: Next.js on Vercel or static host

---

## Scaling Phases

### Phase 1: Foundation (0-1000 users)

**Current State**

**Goals:**
- [x] Baseline monitoring
- [x] Health checks
- [x] Basic alerting
- [ ] 99.5% uptime

**Actions:**
```yaml
# Add to docker-compose for horizontal scaling
api:
  deploy:
    replicas: 2
    resources:
      limits:
        memory: 1G
        cpu: 1000m
```

**Monitoring:**
- Error rate < 1%
- P95 latency < 500ms
- Uptime > 99.5%

---

### Phase 2: Growth (1000-10000 users)

**Goals:**
- [ ] 99.9% uptime
- [ ] P95 latency < 300ms
- [ ] Auto-scaling enabled

**Actions:**

#### 1. API Scaling
```yaml
# Auto-scaling configuration
api:
  autoscaling:
    min_replicas: 2
    max_replicas: 10
    target_cpu_utilization: 70
    target_memory_utilization: 80
```

#### 2. Database Read Replicas
```sql
-- Add read replica
-- In Supabase/Neon: enable replica
-- Or self-hosted:
CREATE replica DATABASE tenderiq_replica;
```

#### 3. Redis Caching
```python
# Add caching layer
from core.cache import cache

@cache(ttl=300)  # 5 minutes
async def get_tender(tender_id):
    return await db.query(Tender, tender_id)
```

**Monitoring:**
- Track cache hit rate (target > 80%)
- Database connection pool usage
- API request queue depth

---

### Phase 3: Scale (10000-100000 users)

**Goals:**
- [ ] 99.95% uptime
- [ ] P99 latency < 500ms
- [ ] Multi-region support

**Actions:**

#### 1. Database Sharding

```python
# Shard by tenant_id
def get_shard(tenant_id: UUID) -> int:
    return hash(tenant_id) % NUM_SHARDS
```

#### 2. Queue Partitioning

```python
# Partition queue by priority
HIGH_PRIORITY = ["notifications", "auth"]
NORMAL = ["ocr", "parsing", "analysis"]
LOW = ["export", "analytics"]
```

#### 3. CDN for Static Assets

```javascript
// next.config.js
module.exports = {
  images: {
    domains: ['cdn.tenderiq.com'],
    path: '/_next/image',
  },
}
```

#### 4. Multi-Region Database

```yaml
# Primary: US-East
# Replica: EU-West, AP-South
# Failover: automatic
```

---

### Phase 4: Enterprise (100000+ users)

**Goals:**
- [ ] 99.99% uptime
- [ ] Global low latency
- [ ] Dedicated infrastructure

**Actions:**

#### 1. Microservices Architecture

```
tenderiq-core/      # Core API
tenderiq-ai/        # AI processing
tenderiq-queue/     # Queue workers
tenderiq-export/    # Export service
tenderiq-analytics/ # Analytics
```

#### 2. Event-Driven Architecture

```python
# Replace direct calls with events
from eventbus import publish

async def process_document(doc_id):
    await publish("document.processed", {
        "document_id": doc_id,
        "status": "queued"
    })
```

#### 3. Advanced Caching

```yaml
# Redis Cluster
# - 6 nodes (3 primary, 3 replica)
# - Automatic sharding
# - 99.99% availability
```

---

## Performance Optimization

### Database

| Optimization | When | Impact |
|--------------|------|--------|
| Add indexes | Phase 2 | 10-100x query speed |
| Read replicas | Phase 2 | 50% read load |
| Connection pooling | Phase 2 | 3x throughput |
| Query optimization | Phase 3 | 2-5x speed |
| Sharding | Phase 4 | Linear scale |

### API

| Optimization | When | Impact |
|--------------|------|--------|
| Add caching | Phase 2 | 10x speed |
| Compression | Phase 2 | 50% bandwidth |
| Pagination | Phase 2 | Memory reduction |
| Async processing | Phase 2 | Throughput 2x |
| WebSockets | Phase 3 | Real-time |

### Frontend

| Optimization | When | Impact |
|--------------|------|--------|
| Code splitting | Phase 1 | Bundle 50% smaller |
| Image optimization | Phase 1 | 70% faster LCP |
| CDN | Phase 2 | Global speed |
| Service worker | Phase 3 | Offline support |

---

## Cost Optimization

### Current Monthly Costs (Est.)

| Service | Cost | Notes |
|---------|------|-------|
| PostgreSQL | $200 | Single instance |
| Redis | $50 | 1GB |
| API Server | $100 | Single instance |
| CDN | $50 | 100GB |
| Sentry | $0 | Free tier |
| **Total** | **~$400** | |

### Cost Reduction Strategies

#### 1. Reserved Instances

```yaml
# Save 40-60%
# Use 1-year reserved for predictable load
```

#### 2. Spot Instances

```yaml
# Save 60-90% for non-critical workers
worker:
  # Only for queue workers
  - spot: true
```

#### 3. Caching Strategy

```
# Cache hit rate > 80%
# Reduces API calls by 60%
# Saves ~$100/month
```

#### 4. Compression

```
# Enable gzip/brotli
# Reduces bandwidth 70%
# Saves ~$30/month
```

---

## Monitoring & Alerting

### Key Metrics

| Metric | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|
| Uptime | 99.5% | 99.9% | 99.99% |
| P95 Latency | 500ms | 300ms | 200ms |
| Error Rate | 1% | 0.5% | 0.1% |
| Queue Depth | <1000 | <500 | <100 |

### Alert Rules

```yaml
# Critical alerts (Page immediately)
- Error rate > 5%
- P99 latency > 2s
- Database down
- API down

# Warning alerts (Email)
- Error rate > 1%
- P95 latency > 500ms
- Queue depth > 1000
- Disk usage > 80%
```

---

## Runbook: Scaling Event

### Step 1: Detect
```bash
# Alert triggered
# Check Grafana/PagerDuty
```

### Step 2: Assess
```bash
# Is it a specific endpoint or all?
# Is it users or system?

curl https://api.tenderiq.com/observability/metrics/summary
```

### Step 3: Respond

**If API overloaded:**
```bash
# Scale API horizontally
kubectl scale deployment api --replicas=5
```

**If database:**
```bash
# Add read replica (5 min)
# Or scale up (2 min)
```

**If queue:**
```bash
# Add worker instances
kubectl scale deployment worker --replicas=5
```

### Step 4: Communicate
```markdown
# Post to status page
# Notify team
# Document incident
```

### Step 5: Post-Mortem
```markdown
# What happened?
# Why?
# How to prevent?
# Timeline
```

---

## Future Considerations

### Phase 5: Global

- Multi-region deployment (3+ regions)
- Edge computing for AI
- Global CDN with 50+ PoPs

### Phase 6: AI Optimization

- Prompt caching
- Fine-tuned models for common tasks
- Local processing for privacy

### Phase 7: Self-Healing

- Automatic failover
- Self-healing infrastructure
- Predictive scaling