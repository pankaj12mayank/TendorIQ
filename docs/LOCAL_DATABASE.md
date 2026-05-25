# Local database (dev)

## Default: SQLite (recommended)

No MySQL install. Data file:

`.tenderiq/data/tenderiq.db`

In `.env`:

```env
DATABASE_DRIVER=sqlite
```

Run:

```bat
run.bat
```

## Optional: MySQL

For production-like local testing:

```env
DATABASE_DRIVER=mysql
MYSQL_PASSWORD=your_root_password
```

See [MYSQL_SETUP.md](./MYSQL_SETUP.md).

Production deploy: always **hosted MySQL** (`DATABASE_DRIVER=mysql`), never SQLite.
