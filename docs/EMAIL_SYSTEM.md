# TenderIQ Email System

Enterprise event-driven transactional email infrastructure.

## Architecture

```
Backend Event → EmailDispatcher → email_queue (DB) → in-process email_process job → Provider chain (SMTP/Resend/Mock)
```

> **Queue runtime:** Jobs are scheduled via `core.tasks.inline.schedule_job` (no Redis worker required).

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
3. All sends go through the **DB queue** (`email_process` inline worker)
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

## Migration & seed (required)

Email tables and default templates are **not** created by the app alone. Before first use:

```bash
cd apps/api && alembic upgrade head
```

Then start the API once so `seed_email_system` runs (or call admin seed endpoints). If seed fails at startup, check MySQL connectivity and that migrations match `apps/api/alembic/versions/`. See [database-migrations.md](database-migrations.md) (layer L2).

## Worker

Email queue items are processed automatically in the API process via the inline task runner.
For manual retries, use `POST /api/v1/email/queue/{id}/retry` (super admin).

## Environment

```env
FRONTEND_URL=http://localhost:3000
ENCRYPTION_KEY=your-32-char-secret-min-32-chars
EMAIL_PROVIDER=resend
EMAIL_API_KEY=re_...          # or RESEND_API_KEY — required when using Resend without Admin SMTP
RESEND_WEBHOOK_SECRET=whsec_...  # Svix signing secret from Resend dashboard
```

### `ENCRYPTION_KEY` rotation (SMTP / provider secrets)

SMTP and provider credentials in `email_provider_configs` are encrypted with Fernet derived from `ENCRYPTION_KEY` (fallback: `JWT_SECRET`). To rotate:

1. Set a new `ENCRYPTION_KEY` in `.env` (32+ characters).
2. Re-save each SMTP/Resend config in **Admin → Email System** so credentials re-encrypt with the new key.
3. Restart API workers / `run.bat` stack.

Old ciphertext cannot be decrypted after rotation until configs are re-entered.

### Resend webhooks

`POST /api/v1/webhooks/resend` updates `email_logs` by `message_id` (delivered, bounced, opened, clicked). Configure the endpoint URL and `RESEND_WEBHOOK_SECRET` in Resend.
