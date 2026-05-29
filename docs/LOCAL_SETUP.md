# Local setup

## System owner (tum — ek hi)

| | |
|--|--|
| **Email (default)** | `admin@tendoriq.com` |
| **Password (default)** | `Owner@ChangeMe123` |
| **Kahan milega** | `d:\Py_Projects\tendoriq\.tenderiq\owner-account.txt` |

`run.bat` ke baad ye file kholo — wahi email/password likha hoga.

**Password change:** Sign in → **Dashboard → Settings → Profile** → *Change password*  
Naya password database mein save hota hai; purana default kaam nahi karega.

Optional: `.env` mein override (sirf pehli seed ke liye):

```env
SYSTEM_OWNER_EMAIL=admin@tendoriq.com
SYSTEM_OWNER_DEFAULT_PASSWORD=Owner@ChangeMe123
```

Login hamesha **database** se hota hai — `.env` se direct login nahi.

Paid/test users sign up from `/sign-up` or are created by the system owner in the admin panel.

## Owner control center quick check

After login with owner account:

1. Open `/dashboard/admin`
2. Verify tabs: CMS Control, Users, Payments, Uploads, Analytics, Pricing
3. Users tab:
   - Suspend / Activate works
   - Delete is **soft delete**
   - Deleted user can be restored from the same tab

## Start

```bat
copy .env.example .env
copy web\.env.local.example web\.env.local
run.bat
```

http://localhost:3000/sign-in

## Naya user

http://localhost:3000/sign-up

## AI (optional)

```env
OPENAI_API_KEY=sk-...
```
