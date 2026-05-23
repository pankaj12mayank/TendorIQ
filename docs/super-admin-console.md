# Super admin console

Platform operators use **`/dashboard/admin`** after signing in at **`/sign-in`** with a `super_admin` role.

## Entry URLs (do not confuse testers)

| URL | Behavior |
|-----|----------|
| `/sign-in` | **Canonical** login for all roles |
| `/dashboard/admin` | Super-admin console (modules via `?module=`) |
| `/admin/login` | **Legacy** — redirects to `/sign-in` |
| `/admin/sign-in` | **Legacy** — same redirect |

Tenant users never use `/dashboard/admin` unless using `?tenant_view=1` for support.

## Modules

| Module | API prefix |
|--------|------------|
| Users | `GET/POST/PATCH/DELETE /api/v1/admin/platform/users` |
| Billing (platform) | `/api/v1/admin/platform/billing` |
| AI providers | `/api/v1/admin/platform/ai-providers` (+ `POST …/test`) |
| Prompts | `/api/v1/prompts` |
| Queue | `/api/v1/admin/platform/queue/jobs` (+ retry/cancel/pause/resume) |
| Failed jobs | `/api/v1/admin/platform/failed-jobs` (dismiss → MySQL `dismissed_failed_jobs`) |
| Audit | `/api/v1/admin/platform/audit-logs` + `POST …/export` |
| Analytics | `/api/v1/admin/platform/analytics/summary` (all tenants) |
| Email system | `/api/v1/email/*` (see [EMAIL_SYSTEM.md](EMAIL_SYSTEM.md)) |

Tenant-scoped audit/export lives at `/api/v1/audit/*` — not the platform audit module.

## AI provider test

`POST …/ai-providers/{id}/test`:

- **Ollama** — HTTP probe to `base_url` (local).
- **OpenAI / Anthropic / Azure / etc.** — checks that an API key exists; does **not** call paid APIs unless configured.

## SSO admin UI

Enterprise SSO settings (`/api/v1/sso/*`) appear when `FEATURE_SSO=true` (and `NEXT_PUBLIC_FEATURE_SSO=true` on web). Default local builds keep SSO off; enable both flags to test SSO in settings.

## Local smoke

```powershell
run.bat check   # includes test_layer10_super_admin.py
cd apps/web
pnpm exec playwright test e2e/super-admin.spec.ts
```
