# Roles & authorization model

## Platform vs tenant

| Kind | Values | Stored in DB | JWT claims |
|------|--------|--------------|------------|
| Platform | `super_admin` | **No** (env credentials only) | `role=super_admin`, no `tenant_id` |
| Tenant membership | `owner`, `admin`, `manager`, `analyst`, `member`, `viewer` | `memberships.role` | `tenant_id`, `membership_role`, `role` (display) |

`users.role` is a profile hint aligned with the user's primary membership. **Never** store `super_admin` on `users.role`.

## UI alias

- `tenant_admin` in the frontend maps to membership `admin` (or `owner`) for navigation and RBAC.
- API `core/roles.py` normalizes aliases before permission checks.

## Demo login

Set in `.env`:

- `DEMO_USER_EMAIL`, `DEMO_USER_PASSWORD`, `DEMO_USER_ROLE` (membership role)
- `DEMO_TENANT_SLUG` (default `demo`), `DEMO_TENANT_NAME`

On login, the API bootstraps tenant + user + membership and issues a JWT with `tenant_id` and `membership_role`.

## Permissions (single matrix)

All roles use the same permission strings as the API `Permission` enum (`tender:create`, `tender:update`, … — not `tender:write`).

| Source | Path |
|--------|------|
| JSON (canonical) | `packages/shared/permissions.json` |
| TypeScript | `@tendoriq/shared/permissions` |
| Python | `apps/api/src/core/rbac.py` (loads JSON) |

Legacy UI aliases (`tender:write` → `tender:update`) are supported in both FE and API checks.

## Code references

- Canonical definitions: `apps/api/src/core/roles.py`
- RBAC matrix loader: `apps/api/src/core/rbac_matrix.py`
- Token issuance: `apps/api/src/api/routers/auth.py` → `issue_access_token`
- Shared types: `packages/shared/src/types/index.ts`
