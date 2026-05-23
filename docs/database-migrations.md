# Database migrations (MySQL)

TenderIQ uses **MySQL 8+** with **Alembic** for schema changes. The API **does not** call `Base.metadata.create_all()` on startup — it only verifies connectivity.

## Fresh install

1. Create the database:

```sql
CREATE DATABASE tenderiq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Set `DATABASE_URL` in the repo root `.env` (see `.env.example`).

3. Apply migrations from `apps/api`:

```bash
cd apps/api
alembic upgrade head
```

Or from the monorepo root:

```bash
pnpm --filter @tendoriq/api run db:migrate
```

## Revision chain

| Revision | Purpose |
|----------|---------|
| `20260522_admin_store` | Full schema from SQLAlchemy models (`create_all`) |
| `20260522_layer1_db_refinements` | Extra indexes / role constraints (idempotent) |

`alembic.ini` defaults are overridden at runtime by `alembic/env.py`, which reads `DATABASE_URL` from app settings (sync `pymysql` driver).

## Soft deletes

Models with `deleted_at` (`SoftDeleteMixin`) are listed via `BaseRepository` with `deleted_at IS NULL`. Deletes set `deleted_at` instead of removing rows (tenders, documents, bids, etc.).
