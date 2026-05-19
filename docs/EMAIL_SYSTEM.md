# TenderIQ Email System

Enterprise event-driven transactional email infrastructure.

## Architecture

```
Backend Event → EmailDispatcher → email_queue (DB) → ARQ email_process → Provider chain (SMTP/Resend/Mock)
```

### Modules (`apps/api/src/core/email/`)

| Module | Purpose |
|--------|---------|
| `db_models.py` | Templates, events, queue, logs, SMTP/Firebase config |
| `events/registry.py` | 30+ canonical event keys |
| `services/dispatcher.py` | Event → template → queue |
| `services/processor.py` | Send with retry (30s / 2m / 10m) |
| `services/password_reset.py` | Secure single-use reset tokens |
| `renderers/template_renderer.py` | `{{variable}}` engine + HTML sanitization |
| `providers/` | SMTP, Resend, mock + fallback chain |
| `crypto.py` | Fernet encryption for credentials |
| `seed.py` | Default templates & event mappings |

## API (`/api/v1/email/`)

Super Admin (Bearer JWT) required except:

- `POST /email/auth/forgot-password`
- `POST /email/auth/reset-password`

| Endpoint | Description |
|----------|-------------|
| `GET/POST /templates` | CRUD + soft archive only |
| `POST /templates/{id}/activate` | Enable template |
| `POST /templates/preview` | Live preview |
| `POST /test-send` | Queue test email |
| `GET/PATCH /events` | Event-template mapping |
| `GET/POST /settings/smtp` | Encrypted SMTP/Resend |
| `PUT /settings/firebase` | Firebase auth email config |
| `GET /logs` | Delivery logs |
| `GET /queue` | Queue monitoring |
| `GET /analytics` | Rates & health |

## Business rules

1. Templates are **never hard deleted** — `archived` + `deleted_at` only
2. Emails only send if **event enabled** AND **template active**
3. All sends go through **async queue** (ARQ `email_process`)
4. Retries: 30s → 2min → 10min → dead letter + admin alert
5. SMTP credentials encrypted with `ENCRYPTION_KEY` / `JWT_SECRET` derived Fernet key

## Admin UI

`/dashboard/admin` → **Email System** module:

- Template editor with variables, preview, test send
- Event manager
- SMTP settings + connection test
- Logs, queue, analytics

## Password reset flow

1. `POST /api/v1/email/auth/forgot-password` `{ email }`
2. Secure token stored (SHA-256 hash), 1h expiry
3. Email `auth.forgot_password` with `{{reset_link}}`
4. User opens `/reset-password?token=...`
5. `POST /api/v1/email/auth/reset-password` `{ token, new_password }`

## Migration

```bash
cd apps/api && alembic upgrade head
```

Revision: `008_email_system`

## Worker

Ensure ARQ worker processes `email_process`:

```bash
python scripts/run_worker.py --queue email
```

## Environment

```env
FRONTEND_URL=http://localhost:3000
ENCRYPTION_KEY=your-32-char-secret
RESEND_API_KEY=re_...   # optional
```
