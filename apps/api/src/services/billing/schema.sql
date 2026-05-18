# Billing Database Schema

## Tables

### plans
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PRIMARY KEY | Plan identifier |
| name | VARCHAR(50) | NOT NULL, UNIQUE | Plan name (free, pro, enterprise) |
| display_name | VARCHAR(100) | NOT NULL | Display name |
| description | TEXT | | Plan description |
| price_monthly | DECIMAL(10,2) | NOT NULL | Monthly price in cents |
| price_annual | DECIMAL(10,2) | NOT NULL | Annual price in cents |
| currency | VARCHAR(3) | DEFAULT 'USD' | Currency code |
| stripe_price_id_monthly | VARCHAR(255) | | Stripe monthly price ID |
| stripe_price_id_annual | VARCHAR(255) | | Stripe annual price ID |
| trial_days | INTEGER | DEFAULT 0 | Trial period in days |
| is_active | BOOLEAN | DEFAULT true | Whether plan is available |
| metadata | JSONB | | Additional plan metadata |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

### plan_features
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PRIMARY KEY | Feature identifier |
| plan_id | UUID | REFERENCES plans(id) | Associated plan |
| feature_key | VARCHAR(100) | NOT NULL | Feature identifier |
| feature_name | VARCHAR(255) | NOT NULL | Display name |
| limit_value | INTEGER | | Limit (null = unlimited) |
| limit_unit | VARCHAR(50) | | Limit type (requests, users, etc.) |
| is_enabled | BOOLEAN | DEFAULT true | Whether feature is enabled |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

### subscriptions
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PRIMARY KEY | Subscription identifier |
| user_id | UUID | NOT NULL, REFERENCES users(id) | User/tenant ID |
| plan_id | UUID | NOT NULL, REFERENCES plans(id) | Current plan |
| status | VARCHAR(50) | NOT NULL | Status (trialing, active, past_due, canceled, unpaid) |
| billing_interval | VARCHAR(20) | NOT NULL | monthly or annual |
| stripe_subscription_id | VARCHAR(255) | | Stripe subscription ID |
| stripe_customer_id | VARCHAR(255) | | Stripe customer ID |
| current_period_start | TIMESTAMP | NOT NULL | Current billing period start |
| current_period_end | TIMESTAMP | NOT NULL | Current billing period end |
| trial_end | TIMESTAMP | | Trial period end |
| cancel_at_period_end | BOOLEAN | DEFAULT false | Cancel at end of period |
| canceled_at | TIMESTAMP | | When subscription was canceled |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

### invoices
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PRIMARY KEY | Invoice identifier |
| subscription_id | UUID | REFERENCES subscriptions(id) | Associated subscription |
| user_id | UUID | NOT NULL, REFERENCES users(id) | User/tenant ID |
| stripe_invoice_id | VARCHAR(255) | | Stripe invoice ID |
| invoice_number | VARCHAR(100) | NOT NULL, UNIQUE | Human-readable invoice number |
| amount | DECIMAL(10,2) | NOT NULL | Total amount in cents |
| currency | VARCHAR(3) | DEFAULT 'USD' | Currency code |
| status | VARCHAR(50) | NOT NULL | paid, pending, failed, refunded, void |
| description | TEXT | | Invoice description |
| paid_at | TIMESTAMP | | Payment timestamp |
| due_date | TIMESTAMP | | Payment due date |
| billing_period_start | TIMESTAMP | | Period start |
| billing_period_end | TIMESTAMP | | Period end |
| metadata | JSONB | | Additional invoice data |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

### payments
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PRIMARY KEY | Payment identifier |
| user_id | UUID | NOT NULL, REFERENCES users(id) | User/tenant ID |
| subscription_id | UUID | REFERENCES subscriptions(id) | Associated subscription |
| invoice_id | UUID | REFERENCES invoices(id) | Associated invoice |
| stripe_payment_intent_id | VARCHAR(255) | | Stripe payment intent ID |
| amount | DECIMAL(10,2) | NOT NULL | Payment amount in cents |
| currency | VARCHAR(3) | DEFAULT 'USD' | Currency code |
| status | VARCHAR(50) | NOT NULL | succeeded, processing, failed, canceled |
| payment_method | VARCHAR(50) | | card, bank_transfer, etc. |
| payment_method_details | JSONB | | Payment method specific details |
| failure_code | VARCHAR(100) | | Failure error code |
| failure_message | TEXT | | Failure error message |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

### payment_methods
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PRIMARY KEY | Payment method identifier |
| user_id | UUID | NOT NULL, REFERENCES users(id) | User/tenant ID |
| stripe_payment_method_id | VARCHAR(255) | NOT NULL | Stripe payment method ID |
| type | VARCHAR(50) | NOT NULL | card, bank_account |
| brand | VARCHAR(50) | | card brand (visa, mastercard, etc.) |
| last4 | VARCHAR(4) | | Last 4 digits |
| expiry_month | INTEGER | | Card expiry month |
| expiry_year | INTEGER | | Card expiry year |
| bank_name | VARCHAR(255) | | Bank name for bank accounts |
| is_default | BOOLEAN | DEFAULT false | Default payment method |
| is_active | BOOLEAN | DEFAULT true | Whether method is active |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

### usage_records
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PRIMARY KEY | Record identifier |
| user_id | UUID | NOT NULL, REFERENCES users(id) | User/tenant ID |
| subscription_id | UUID | REFERENCES subscriptions(id) | Associated subscription |
| feature_key | VARCHAR(100) | NOT NULL | Feature being tracked |
| count | INTEGER | NOT NULL | Usage count |
| period_start | TIMESTAMP | NOT NULL | Period start date |
| period_end | TIMESTAMP | NOT NULL | Period end date |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

### plan_change_history
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PRIMARY KEY | Change identifier |
| user_id | UUID | NOT NULL, REFERENCES users(id) | User/tenant ID |
| subscription_id | UUID | REFERENCES subscriptions(id) | Associated subscription |
| from_plan_id | UUID | REFERENCES plans(id) | Previous plan |
| to_plan_id | UUID | REFERENCES plans(id) | New plan |
| change_type | VARCHAR(50) | NOT NULL | upgrade, downgrade, cancel, reactivate |
| effective_date | TIMESTAMP | NOT NULL | When change takes effect |
| processed_at | TIMESTAMP | | When change was processed |
| reason | TEXT | | Reason for change |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

## Indexes
- subscriptions(user_id, status)
- subscriptions(stripe_subscription_id)
- invoices(user_id, status)
- invoices(subscription_id)
- usage_records(user_id, feature_key, period_start)
- plan_change_history(user_id, created_at)

## Row Level Security
- Users can only access their own billing data
- Admin users can access all billing data

## Functions

### get_plan_limits(plan_id)
Returns JSON object with all feature limits for a plan.

### check_usage_quota(user_id, feature_key)
Returns true if user has not exceeded quota for feature.

### calculate_proration(subscription_id, new_plan_id)
Calculates proration amount for plan change.