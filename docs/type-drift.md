# Type drift policy

Canonical TypeScript types live in **`@tendoriq/shared`**. App code should import mappers and enums from shared instead of redefining them.

## Modules

| Module | Purpose |
|--------|---------|
| `@tendoriq/shared/types` | Zod schemas (`User`, `Tender`, onboarding steps) |
| `@tendoriq/shared/tenders` | `ApiTender` / `ClientTender` + `mapTenderFromApi` |
| `@tendoriq/shared/roles` | `MembershipRole`, `AdminConsoleRole`, `normalizeDisplayRole` |
| `@tendoriq/shared/plans` | `normalizePlanId`, `normalizeBillingCycle` |
| `@tendoriq/shared/notifications` | `mapApiNotification` (snake_case ↔ UI) |
| `@tendoriq/shared/auth` | `SessionUser` for browser session storage |
| `@tendoriq/shared/permissions` | RBAC matrix (same JSON as API `rbac.py`) |

## Rules

1. **API field names** — Accept both snake_case and camelCase in mappers; emit camelCase for UI.
2. **Tenant scope** — Prefer `tenantId`; `organizationId` is a deprecated alias only.
3. **Roles** — DB membership roles are `owner | admin | manager | analyst | member | viewer`. Platform role is `super_admin` (JWT only).
4. **Plans** — API/onboarding canonical ids: `free`, `starter`, `professional`, `enterprise`. UI may send `plan_pro` / `annual`; always run through `normalizePlanId` / `normalizeBillingCycle`.
5. **New surfaces** — Add shared mapper first, then thin re-exports under `apps/web/src/lib/*`.

## Analysis (L35)

| Module | Purpose |
|--------|---------|
| `@tendoriq/shared/analysis` | `parseAnalysisDashboard` — permissive Zod for API JSON |
| `apps/web/src/lib/analysis-mapper.ts` | Maps dashboard payload → `TenderAnalysis` UI types (`keyFindings` → `keyHighlights`, etc.) |

## Python

API enums and `permissions.json` must stay aligned with shared JSON. Use `core/tenant_types.py` (`TenantId`, `UserId`, `parse_tenant_uuid`) for tenant-scoped IDs. Layer tests under `apps/api/tests/unit/test_layer*_*.py` guard structural drift.
