# TenderIQ Design System

Enterprise-grade UI for procurement, tender, and compliance workflows.

## Foundations

| Layer | Location |
|-------|----------|
| CSS tokens | `apps/web/src/app/globals.css` |
| Tailwind | `apps/web/tailwind.config.ts` |
| Motion presets | `apps/web/src/design-system/motion.ts` |
| Icon map | `apps/web/src/design-system/icons.ts` |
| Typography | `apps/web/src/design-system/typography.ts` |

## Typography

- **Sans:** Inter (`--font-sans`) — body, tables, forms
- **Display:** Plus Jakarta Sans (`--font-display`) — headings, KPI values

Utility classes: `font-display`, `text-gradient-brand`

## Colors (semantic)

- `primary` — brand / trust
- `success`, `warning`, `info`, `destructive` — status + actions
- `background`, `card`, `muted`, `accent` — surfaces

## Components (`@/components/design-system`)

| Component | Use |
|-----------|-----|
| `AppSidebar` | Role-based collapsible navigation |
| `PageHeader`, `Breadcrumbs` | Page titles |
| `KpiCard` | Dashboard metrics |
| `StatusBadge`, `StatusDot` | Tender/job status |
| `DataTableShell` + table primitives | Enterprise tables |
| `AiProcessingPipeline` | OCR / extraction / risk flows |
| `PremiumEmptyState` | Empty & error states |
| `Skeleton`, `KpiSkeleton` | Loading |

## Roles

Navigation groups in `roleNavGroups`:

- **super_admin** — Admin console, analytics
- **tenant_admin** — Full workspace + billing + team
- **user** — Tenders, bids, upload

## Auth flows

1. Super Admin → `/admin/login` (`.env` credentials)
2. Tenant → Clerk sign-up → `/onboarding` → dashboard
3. Team → invited by tenant admin (plan limits)

## Usage

```tsx
import { KpiCard, PageHeader, StatusBadge } from '@/components/design-system';
```

Use surface utilities: `surface-card`, `surface-glass`, `scroll-premium`, `sticky-header-shadow`.
