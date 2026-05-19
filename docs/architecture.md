# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (React)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Dashboard  │  │  Documents  │  │  Admin Panel            │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼──────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Authentication │ Rate Limiting │ Tenant Isolation      │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Core APIs    │    │   Queue       │    │   AI Service  │
│  - Tenders    │    │   Workers     │    │   - OpenAI    │
│  - Documents  │    │   - OCR       │    │   - Anthropic │
│  - Bids       │    │   - Parsing   │    │   - Azure     │
│  - Export     │    │   - Analysis  │    │   - Ollama    │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  PostgreSQL   │    │    Redis      │    │  Sentry/      │
│  (Primary DB) │    │  (Queue+Cache)│    │  Monitoring   │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## Components

### Frontend (apps/web)

```
web/
├── app/
│   ├── (auth)/          # Login, signup
│   ├── (dashboard)/     # Main app
│   │   ├── tenders/     # Tender management
│   │   ├── documents/   # Document viewer
│   │   ├── analytics/   # Reports
│   │   └── admin/       # Admin panel
│   └── api/             # API routes
├── components/
│   ├── ui/              # Base UI components
│   ├── tenders/         # Tender-specific
│   ├── documents/       # Document components
│   └── admin/           # Admin components
├── hooks/               # Custom React hooks
└── lib/                 # Utilities
```

**Key Libraries:**
- React 18 + Next.js 14
- TanStack Query (data fetching)
- TanStack Table (data tables)
- React Hook Form + Zod
- Tailwind CSS

---

### Backend (apps/api)

```
api/src/
├── api/
│   ├── routers/         # Route handlers
│   │   ├── tenders.py
│   │   ├── documents.py
│   │   ├── ai.py
│   │   ├── queue.py
│   │   ├── billing.py
│   │   └── audit.py
│   ├── dependencies/    # FastAPI dependencies
│   │   ├── auth.py
│   │   ├── permissions.py
│   │   └── audit.py
│   └── schemas/         # Pydantic models
├── core/
│   ├── models.py        # SQLAlchemy models
│   ├── auth.py          # JWT handling
│   ├── rbac.py          # Role-based access
│   ├── tenant_middleware.py
│   ├── queue/           # ARQ queue
│   ├── ai/              # AI providers
│   └── export/          # Export handlers
└── main.py              # Entry point
```

**Key Libraries:**
- FastAPI + Pydantic
- SQLAlchemy + asyncpg
- ARQ (Redis queue)
- Sentry SDK

---

## Data Flow

### 1. Document Upload

```
User → Frontend → API → Redis Queue → Worker → PostgreSQL
                              ↓
                         S3 Storage
```

1. User uploads file via frontend
2. API validates and stores in Redis queue
3. Worker picks up job, processes (OCR/parsing)
4. Results stored in PostgreSQL
5. User notified via WebSocket/polling

### 2. AI Analysis

```
User → API → Queue → AI Worker → LLM API → Store Results
              ↓
         Sentry (error tracking)
```

1. User requests analysis
2. Job queued in Redis
3. Worker calls configured LLM
4. Results stored in PostgreSQL
5. Error tracking via Sentry

### 3. Tenant Isolation

```
Request → Middleware → Extract Tenant ID → Validate → Query
     ↓
  Audit Log
```

1. Every request goes through TenantMiddleware
2. tenant_id extracted from JWT
3. All queries filtered by tenant_id
4. All actions logged to audit_logs table

---

## Security Architecture

### Authentication Flow

```
┌──────────┐    ┌─────────┐    ┌──────────┐    ┌────────────┐
│  Clerk   │───▶│  JWT    │───▶│  Verify  │───▶│  AuthCtx   │
│  Login   │    │  Token  │    │  Token   │    │  Context   │
└──────────┘    └─────────┘    └──────────┘    └────────────┘
```

### Authorization (RBAC)

```
User Role → Permission Matrix → Resource Access
   ↓
Permission Check
```

- 6 roles: super_admin, admin, manager, analyst, viewer
- 20+ permissions across resources

---

## Database Schema

### Key Models

```
users
├── id (UUID)
├── clerk_id
├── email
├── role
└── tenant_id

tenants
├── id (UUID)
├── name
├── plan
├── billing_cycle
└── limits

tenders
├── id (UUID)
├── tenant_id (FK)
├── title
├── status
├── deadline
└── created_by (FK)

documents
├── id (UUID)
├── tender_id (FK)
├── tenant_id (FK)
├── file_path
├── status (processing_status)
└── metadata (JSONB)

audit_logs
├── id (UUID)
├── tenant_id (FK)
├── user_id (FK)
├── action
├── action_type
├── resource_type
└── changes (JSONB)
```

---

## Queue Architecture

### Queues

| Queue | Purpose | Priority |
|-------|---------|----------|
| `ocr` | OCR processing | Normal |
| `parsing` | Document parsing | Normal |
| `analysis` | AI analysis | Normal |
| `export` | Report generation | Low |
| `notifications` | Email/push | High |

### Job Lifecycle

```
Queued → Active → Completed
       ↘ Failed → Retry (3x) → Dead Letter
```

---

## Monitoring Stack

| Tool | Purpose |
|------|---------|
| Sentry | Error tracking |
| Custom Metrics | API, queue, AI metrics |
| Health Checks | Service availability |
| Audit Logs | Security compliance |

---

## Scaling Strategy

### Horizontal Scaling

- Multiple API instances behind load balancer
- Stateless design (all state in DB/Redis)
- Sticky sessions for WebSocket

### Vertical Scaling

- Increase worker processes
- Connection pooling
- Redis caching

### Database Scaling

- Read replicas for queries
- PgBouncer for connection pooling
- Redis cache for hot data

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│                  Load Balancer                  │
│                   (Cloudflare)                  │
└────────────────────┬────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   ┌─────────┐          ┌─────────┐
   │  API 1  │          │  API 2  │
   └────┬────┘          └────┬────┘
        │                    │
        └────────┬───────────┘
                 ▼
         ┌──────────────┐
         │    Redis     │
         │  (Queue +    │
         │   Cache)     │
         └──────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   ┌─────────┐      ┌─────────┐
   │  DB 1   │      │  DB 2   │
   │(Primary)│      │(Replica)│
   └─────────┘      └─────────┘
```

---

## Technology Decisions

| Decision | Reason |
|----------|--------|
| FastAPI | High performance, async, auto-docs |
| PostgreSQL | ACID, JSONB, full-text search |
| Redis | Queue, caching, sessions |
| Clerk | Secure, scalable auth |
| TanStack Query | Caching, optimistic updates |
| Tailwind | Rapid development, consistency |