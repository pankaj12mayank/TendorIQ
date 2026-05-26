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

## Demo user (testing — owner nahi)

| | |
|--|--|
| Email | `demo@tendoriq.com` |
| Password (default) | `Demo@ChangeMe123` |

Details: `.tenderiq/bootstrap-credentials.json` (same folder as owner file)

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
