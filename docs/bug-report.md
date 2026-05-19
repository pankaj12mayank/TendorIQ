# Bug Report - Production QA Audit

**Date:** 2026-05-19
**Total Issues:** 18
**Critical:** 3 | High: 5 | Medium: 7 | Low: 3

---

## Critical (3)

### BUG-001: Billing Plan Limits Not Enforced
**Severity:** Critical | **Area:** Billing
**Description:** No validation of plan limits before allowing operations. Users can exceed document counts, API calls, storage without restriction.
**Impact:** Revenue loss, resource exhaustion
**Affected Code:** `core/ai/service.py`, `api/routers/documents.py`
**Fix Required:** Add `check_plan_limit(tenant_id, resource_type)` middleware

### BUG-002: React App Has No Error Boundary
**Severity:** Critical | **Area:** Frontend
**Description:** Uncaught errors crash entire application. No ErrorBoundary component exists.
**Impact:** Users see blank screen on any error
**Affected Code:** `apps/web/src/app/` - root layout
**Fix Required:** Wrap app with ErrorBoundary component

### BUG-003: Tenant ID Can Be None in Queries
**Severity:** Critical | **Area:** Security
**Description:** 54 locations have `tenant_id: Optional` which can allow cross-tenant data access
**Impact:** Data breach potential
**Affected Code:** Multiple services
**Fix Required:** Make tenant_id required in tenant-scoped queries

---

## High (5)

### BUG-004: AI Spending Limit Checked But Not Enforced
**Severity:** High | **Area:** AI
**Description:** `check_spending_limit()` returns warning but doesn't block requests
**Impact:** Uncontrolled AI costs
**Affected Code:** `core/ai/accounting.py:203`

### BUG-005: OCR Missing Max Retries Validation
**Severity:** High | **Area:** OCR
**Description:** No check for max retries before queuing OCR job
**Impact:** Infinite retry loops
**Affected Code:** `api/routers/ocr.py`

### BUG-006: No Export Timeout Handling
**Severity:** High | **Area:** Export
**Description:** Large exports can hang indefinitely
**Impact:** User frustration, resource blocking
**Affected Code:** `core/export/`

### BUG-007: Upload Flow Missing Virus Scan
**Severity:** High | **Area:** Security
**Description:** No file scanning for malicious content
**Impact:** System security risk
**Affected Code:** `api/routers/files.py`

### BUG-008: Session Expiry Not Handled Gracefully
**Severity:** High | **Area:** Frontend
**Description:** Session timeout redirects to login, losing user state
**Impact:** Poor UX
**Affected Code:** `hooks/use-auth.tsx`

---

## Medium (7)

### BUG-009: Duplicate Health Endpoints
**Severity:** Medium | **Area:** API
**Description:** Health endpoints exist in multiple routers
**Affected Code:** `api/health.py`, `api/router/observability.py`

### BUG-010: Queue Retry Has No Exponential Backoff
**Severity:** Medium | **Area:** Queue
**Description:** Immediate retry without delay
**Impact:** API overload on failures

### BUG-011: Missing Global Loading Indicator
**Severity:** Medium | **Area:** Frontend
**Description:** No global loading state indicator
**Impact:** User confusion during navigation

### BUG-012: API Response No Compression Headers
**Severity:** Medium | **Area:** Performance
**Description:** Missing cache-control headers
**Impact:** Performance

### BUG-013: Charts Missing Loading Skeletons
**Severity:** Medium | **Area:** Frontend
**Description:** Charts show nothing while loading
**Impact:** UX

### BUG-014: Deep Links Lose State After Session Expiry
**Severity:** Medium | **Area:** Frontend
**Description:** URL parameters lost on re-auth
**Impact:** UX

### BUG-015: Some Errors Only Logged to Console
**Severity:** Medium | **Area:** Error Handling
**Description:** Not all API errors surfaced to user
**Impact:** Debugging difficulty

---

## Low (3)

### BUG-016: Hardcoded Health Check Interval
**Severity:** Low | **Area:** Config
**Description:** 30s interval hardcoded in two places

### BUG-017: No Alert for Stuck Jobs > 10min
**Severity:** Low | **Area:** Monitoring
**Description:** Missing alerting rule

### BUG-018: CORS Origins Not Validated
**Severity:** Low | **Area:** Config
**Description:** No validation of CORS origins format

---

## Summary by Component

| Component | Critical | High | Medium | Low |
|-----------|----------|------|--------|-----|
| Billing | 1 | 1 | 0 | 0 |
| Frontend | 1 | 1 | 3 | 0 |
| Security | 1 | 1 | 0 | 1 |
| AI | 0 | 1 | 0 | 0 |
| Queue | 0 | 1 | 1 | 1 |
| API | 0 | 0 | 2 | 0 |
| Export | 0 | 1 | 0 | 0 |
| Monitoring | 0 | 0 | 0 | 1 |

---

## Recommended Priority Order

1. **P0 (Today):** BUG-001, BUG-002, BUG-003
2. **P1 (This Week):** BUG-004, BUG-005, BUG-006, BUG-008
3. **P2 (Before Launch):** BUG-007, BUG-009, BUG-010
4. **P3 (Post-Launch):** All others