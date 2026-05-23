# Billing, Stripe webhooks & quota tracking

## Tenant billing (`/dashboard/billing`)

- Plans and subscription: `GET/POST /api/v1/billing/*`
- Requires a tenant user with `analytics:view` (or admin role).
- Seed data: run `alembic upgrade head` and complete onboarding (step 4 sets plan).

## Stripe webhooks

- Endpoint: `POST /api/v1/webhooks/stripe`
- Set `STRIPE_WEBHOOK_SECRET` in `.env` (from Stripe CLI or Dashboard).
- Handled events: `checkout.session.completed`, `customer.subscription.*`, `invoice.paid`
- Checkout metadata should include `tenant_id` and optional `plan_id` for reliable sync.

Local forward:

```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

## Quota enforcement (`POST /api/v1/billing/usage/track`)

1. Sign in as a tenant user with a workspace.
2. `GET /api/v1/billing/quota` — note `featureKey` and `remaining`.
3. `POST /api/v1/billing/usage/track` with `{ "feature_key": "tenders", "quantity": 1 }`.
4. Re-fetch quota — `used` should increase (subject to plan limits).

The usage dashboard (`/dashboard/usage`) reads the same quota API.

## Razorpay (optional)

Razorpay keys in `.env.example` enable alternate checkout via `core/payments` when both keys are set. Stripe remains the primary path for subscription webhooks.
