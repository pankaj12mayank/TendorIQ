# Local setup — simple (no cloud keys)

## Env files (keep in sync)

| File | Purpose |
|------|---------|
| `.env.example` | Template — copy to `.env` |
| `.env` | API + shared secrets (repo root) |
| `web/.env.local.example` | Template — copy to `web/.env.local` |
| `web/.env.local` | Next.js public vars only |

Same keys, same order in `.env` and `.env.example`. After editing one, mirror changes in the other.

```bat
copy .env.example .env
copy web\.env.local.example web\.env.local
```

## Start

```bat
cd d:\Py_Projects\tendoriq
run.bat
```

Open http://localhost:3000/sign-in

| Account | Email | Password |
|---------|--------|----------|
| **Admin** | `admin@tenderiq.com` | `SuperAdmin@123` |
| **Demo user** | `demo@tenderiq.com` | `Demo@123` |

No Supabase, no Clerk, no API keys required for login.

---

## Optional: AI analysis

Add **one** key to root `.env`, restart API:

```env
OPENAI_API_KEY=sk-...
```

Then Upload → pick model → analyze.

---

## Later: real Supabase keys (production-style login)

1. https://supabase.com → **New project** (free tier OK)
2. **Project Settings → API**
   - **Project URL** → `SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_URL`
   - **anon public** → `SUPABASE_ANON_KEY` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **JWT Secret** (same page or JWT settings) → `SUPABASE_JWT_SECRET` (API only)
3. Root `.env`:

```env
AUTH_PROVIDER=supabase
SUPABASE_URL=https://YOUR_REF.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret
NEXT_PUBLIC_AUTH_PROVIDER=supabase
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_REF.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

4. `web/.env.local` — same `NEXT_PUBLIC_*` values
5. `run.bat stop` → `run.bat`
6. Sign up at `/sign-up` (Supabase handles email)

---

## Later: Clerk keys

1. https://dashboard.clerk.com → application → **API Keys**
2. `.env`:

```env
AUTH_PROVIDER=clerk
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

3. `web/.env.local`:

```env
NEXT_PUBLIC_AUTH_PROVIDER=clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
```

---

## Later: Razorpay (billing test)

1. https://dashboard.razorpay.com → **Test mode** keys
2. `.env`: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`
3. Settings → Billing → Pay with Razorpay

---

**Rule:** Jab tak real keys na ho, `AUTH_PROVIDER=local` rakho — app automatically local mode use karti hai agar Supabase/Clerk keys khali ya placeholder hon.
