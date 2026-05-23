# File storage

TenderIQ stores uploads under tenant-scoped keys: `{tenant_id}/{category}/{date}/...`.

## Providers (`STORAGE_PROVIDER`)

| Value | Use case |
|-------|----------|
| `local` | Default dev — files on disk under `STORAGE_LOCAL_PATH` (no AWS credentials) |
| `s3` | AWS S3 or S3-compatible endpoint |
| `r2` | Cloudflare R2 |

S3/R2 calls use **boto3 in `asyncio.to_thread`** so the FastAPI event loop is not blocked.

## Local development

```env
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=./uploads
STORAGE_TOKEN_CLOCK_SKEW_SECONDS=120
```

**Path resolution:** Relative `STORAGE_LOCAL_PATH` values are resolved against `apps/api` (not the shell CWD), so `./uploads` is stable on Windows and Linux. The API creates the directory on startup when `STORAGE_PROVIDER=local`.

**Signed URL clock skew:** Local blob tokens (`?token=...`) accept expiry up to `STORAGE_TOKEN_CLOCK_SKEW_SECONDS` after the nominal `expires_at`, so minor client/server clock drift does not break uploads mid-flight.

Signed upload/download URLs point at tokenized API routes:

- `PUT /api/v1/files/blob/{storage_key}?token=...`
- `GET /api/v1/files/blob/{storage_key}?token=...`

The web app prefers `POST /api/v1/files/upload/direct` first, which works with local disk without presign.

## Limits

Configured via `STORAGE_MAX_FILE_SIZE_MB` and `STORAGE_ALLOWED_EXTENSIONS` (see `.env.example`).

## Security

- Keys must start with the caller's `tenant_id/` (`assert_tenant_storage_key`).
- Path segments `..` are rejected.
