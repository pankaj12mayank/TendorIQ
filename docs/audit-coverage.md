# Audit logging coverage

Tenant mutations should write rows to `audit_logs` via `tenant_audit` or `audit_logger` in `apps/api/src/api/dependencies/audit.py`.

## Covered flows

| Area | Actions | `action_type` |
|------|---------|----------------|
| Auth | login (tenant users) | `auth` |
| Tenders | create, update, delete | `tender` |
| Documents | upload complete, delete | `upload` / `document` |
| Review workflow | state changes | varies |
| RBAC | access denied | `admin_action` |
| Tenant audit export | export | `export` |
| Platform admin | list/export (capped) | — |

## Limits

Defined in `apps/api/src/core/audit_limits.py` and mirrored in `apps/web/src/lib/audit-constants.ts`:

- List default: **100** rows (max **500** per request)
- Export max: **5000** rows per export

Platform export accepts optional `limit` in the POST body; the admin UI sends `PLATFORM_AUDIT_EXPORT_MAX_ROWS`.

## Adding new coverage

1. Call `tenant_audit.log_create|log_update|log_delete` from the router after a successful mutation.
2. Pass `request` when available for IP / user-agent capture.
3. On failure, log a warning — do not fail the user mutation.
4. Extend `test_layer33_audit_coverage.py` with a static check for the router path.
