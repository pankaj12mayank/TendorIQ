# TenderIQ API Documentation

**Version:** 1.0.0
**Base URL:** `https://api.tenderiq.com/v1`

---

## Authentication

All API requests require authentication via JWT token in the Authorization header:

```bash
Authorization: Bearer <JWT_TOKEN>
```

### Getting a Token

1. Use Clerk to sign in
2. JWT is returned in the session
3. Include it in subsequent requests

---

## Endpoints

### Health Check

```
GET /health
GET /health/ready
GET /health/live
```

**Response:**
```json
{
  "status": "healthy",
  "environment": "production"
}
```

---

### Tenders

#### List Tenders

```
GET /tenders
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| limit | int | Items per page (default: 20) |
| status | string | Filter by status |
| search | string | Search in title/description |

**Response:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

#### Get Tender

```
GET /tenders/{tender_id}
```

#### Create Tender

```
POST /tenders
```

**Body:**
```json
{
  "title": "IT Infrastructure Services",
  "description": "Government tender for IT services",
  "deadline": "2026-06-30T23:59:59Z",
  "budget": 500000,
  "category": "services"
}
```

---

### Documents

#### Upload Document

```
POST /documents/upload
```

**Body:** multipart/form-data
- file: Binary file
- tender_id: UUID (optional)

**Response:**
```json
{
  "document_id": "uuid",
  "status": "uploaded",
  "size": 2048576
}
```

#### Get Document

```
GET /documents/{document_id}
```

#### Delete Document

```
DELETE /documents/{document_id}
```

---

### AI Analysis

#### Analyze Document

```
POST /ai/analyze
```

**Body:**
```json
{
  "document_id": "uuid",
  "analysis_type": "risk|summary|extraction",
  "prompt_id": "uuid (optional)"
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

#### Get Analysis Result

```
GET /ai/analysis/{job_id}
```

---

### OCR

#### Submit OCR

```
POST /ocr/submit
```

**Body:**
```json
{
  "document_id": "uuid"
}
```

#### Get OCR Status

```
GET /ocr/status/{job_id}
```

---

### Queue

#### Get Queue Stats

```
GET /queue/stats
```

**Response:**
```json
{
  "queues": {
    "ocr": {"pending": 5, "active": 2, "completed": 100},
    "parsing": {"pending": 3, "active": 1, "completed": 50}
  }
}
```

#### Retry Failed Job

```
POST /queue/failed/{job_id}/retry
```

---

### Billing

#### Get Subscription

```
GET /billing/subscription
```

**Response:**
```json
{
  "plan": "enterprise",
  "billing_cycle": "monthly",
  "status": "active",
  "limits": {
    "users": -1,
    "documents": -1,
    "api_calls": -1
  }
}
```

---

### Audit Logs

```
GET /audit/logs
```

**Query Parameters:**
| Parameter | Description |
|-----------|-------------|
| action_type | Filter: upload, delete, export, admin_action, ai_generation, billing |
| user_id | Filter by user |
| start_date | Filter start |
| end_date | Filter end |
| search | Search text |
| limit | Max results (default: 50) |

---

### Observability

#### Get Metrics Summary

```
GET /observability/metrics/summary
```

#### Get API Metrics

```
GET /observability/metrics/api
```

#### Get Queue Metrics

```
GET /observability/metrics/queue
```

#### Get AI Metrics

```
GET /observability/metrics/ai
```

#### Get Processing Metrics

```
GET /observability/metrics/processing
```

#### Get Failure Metrics

```
GET /observability/metrics/failures
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "field": "field_name (optional)"
}
```

### Common Status Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable - Validation error |
| 429 | Too Many Requests - Rate limited |
| 500 | Internal Error - Server error |
| 503 | Service Unavailable |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| General | 100/minute |
| AI Endpoints | 20/minute |
| Upload | 10/minute |

---

## Webhooks

### Stripe Webhooks

```
POST /webhooks/stripe
```

Events:
- `invoice.paid`
- `customer.subscription.updated`
- `customer.subscription.deleted`

---

## SDK

### JavaScript/TypeScript

```typescript
import { TenderIQ } from '@tendoriq/sdk';

const client = new TenderIQ({
  apiKey: process.env.TENDERIQ_API_KEY,
});

const tenders = await client.tenders.list();
```

### Python

```python
from tenderiq import TenderIQ

client = TenderIQ(api_key=os.getenv("TENDERIQ_API_KEY"))

tenders = client.tenders.list()
```