# MySQL setup

TenderIQ uses **MySQL only**. Background jobs (email, OCR) run **in-process** in the API — no Redis, Docker, or PostgreSQL.

## Database

```sql
CREATE DATABASE tenderiq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```env
DATABASE_URL=mysql+aiomysql://root:YOUR_PASSWORD@localhost:3306/tenderiq?charset=utf8mb4
```

## Start

```bat
run.bat
```

Tables are created on API startup via SQLAlchemy `create_all`.

## Removed stack

| Removed | Replacement |
|---------|-------------|
| PostgreSQL | MySQL |
| Redis / ARQ | `core.tasks.inline` (asyncio) |
| Docker Compose | `run.bat` local start |
