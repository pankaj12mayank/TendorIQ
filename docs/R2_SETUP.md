# Cloudflare R2 setup (Phase 3)

## 1. Create bucket

1. Cloudflare Dashboard → R2 → Create bucket (e.g. `tendoriq-uploads`).
2. Create API token with **Object Read & Write** on that bucket.

## 2. `.env` (repo root)

```env
STORAGE_PROVIDER=r2
STORAGE_BUCKET=tendoriq-uploads
R2_ACCOUNT_ID=<account-id>
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<secret>
STORAGE_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com
STORAGE_MAX_FILE_SIZE_MB=25
STORAGE_ALLOWED_EXTENSIONS=.pdf,.doc,.docx
```

## 3. CORS (required for browser presigned PUT)

In R2 bucket → Settings → CORS policy:

```json
[
  {
    "AllowedOrigins": ["http://localhost:3000", "https://your-app.vercel.app"],
    "AllowedMethods": ["GET", "PUT", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

## 4. Verify

1. `run.bat` → sign in → `/dashboard/upload`
2. Upload a PDF &lt; 25MB
3. Network tab: `POST .../upload/initiate` → `PUT` to `*.r2.cloudflarestorage.com` → `POST .../upload/complete`

Local dev without R2: keep `STORAGE_PROVIDER=local` (direct upload, no CORS).

## Notes

- Same storage config is also used for owner CMS assets (story logos, workflow images, branding uploads).
