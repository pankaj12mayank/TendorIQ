# Local setup

## System owner account

| | |
|--|--|
| **Email (default)** | `admin@tendoriq.com` |
| **Password (default)** | `Owner@ChangeMe123` |
| **File location** | `.tenderiq/owner-account.txt` (after first `pnpm setup`) |

Open `.tenderiq/owner-account.txt` after running `pnpm setup` for the actual credentials.

**Password change:** Sign in → **Dashboard → Settings → Profile** → *Change password*

Optional: `.env` override (first seed only):

```env
SYSTEM_OWNER_EMAIL=admin@tendoriq.com
SYSTEM_OWNER_DEFAULT_PASSWORD=Owner@ChangeMe123
```

Login always uses the **database** — `.env` is not used for direct login.

## Owner control center

After login with owner account:

1. Open `/dashboard/admin`
2. Verify tabs: CMS Control, Users, Payments, Uploads, Analytics, Pricing

## Start

```bash
pnpm setup
pnpm dev
```

http://localhost:3000/sign-in

## New user signup

http://localhost:3000/sign-up

## AI (optional)

```env
OPENAI_API_KEY=sk-...
```
