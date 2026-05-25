# MySQL setup (optional local dev)

> **Default dev database is SQLite** — no MySQL needed. See [LOCAL_DATABASE.md](./LOCAL_DATABASE.md).  
> Use this guide only if you set `DATABASE_DRIVER=mysql` in `.env`.

TenderIQ uses **MySQL** when you choose the mysql driver. No Docker required.

**Production:** Frontend on **Vercel**; API + database on your host (e.g. free/cheap PaaS). Set `DATABASE_URL` there to your hosted MySQL connection string — same format as below.

---

## 1. MySQL on Windows (automatic via `run.bat`)

**`run.bat` tries for you:**

1. Start **MySQL80** / **MariaDB** service if already installed  
2. If nothing on port 3306 → **winget** install (MariaDB or MySQL; **Admin** prompt once)  
3. If `.env` still has placeholder password → set dev URL with password **`TenderIQ@Dev123`**

When the MySQL installer asks for a root password, use **`TenderIQ@Dev123`** (same as `.env.example`), or change `.env` to match what you chose.

Skip auto-install: `set TENDERIQ_AUTO_MYSQL_INSTALL=0`  
Skip entirely: `set TENDERIQ_SKIP_MYSQL_INSTALL=1`

### Manual install (if winget fails)

- [MySQL Installer](https://dev.mysql.com/downloads/installer/), or `winget install Oracle.MySQL`
- **Services** → **MySQL80** → **Start**
- `.env`: `DATABASE_URL=mysql+aiomysql://root:YOUR_PASSWORD@localhost:3306/tenderiq?charset=utf8mb4`  
  (`@` in password → `%40` in the URL)

```powershell
Test-NetConnection -ComputerName localhost -Port 3306
```

---

## 2. Create database (optional)

`run.bat` can create `tenderiq` for you. To create manually in MySQL Workbench or CLI:

```sql
CREATE DATABASE IF NOT EXISTS tenderiq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 3. Configure `.env`

Copy template if needed:

```bat
copy .env.example .env
```

Set your MySQL root password here (**`@` is fine — no URL encoding**):

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=Myproduct@12
MYSQL_DATABASE=tenderiq
```

The API builds `DATABASE_URL` from `MYSQL_PASSWORD` automatically.

---

## 4. Start the app

```bat
run.bat
```

`run.bat` checks MySQL, creates the DB if missing, and runs **`alembic upgrade head`**.

Manual migration (from `apps/api`, with repo `.env`):

```bat
set DOTENV_PATH=D:\Py_Projects\tendoriq\.env
python -m alembic upgrade head
```

See [database-migrations.md](./database-migrations.md).

---

## Troubleshooting

| Error | Fix |
|--------|-----|
| `Can't connect ... actively refused` | Start **MySQL80** service |
| `Access denied for user 'root'` | Wrong password in `.env` |
| `changeme` warning | Replace placeholder in `DATABASE_URL` |
| **`1045 Access denied`** | MySQL is running but **password wrong** — put your real root password in `.env` (`@` → `%40`) |
| Login fails after API starts | MySQL must be up; check `.tenderiq/startup.log` |

### Access denied (1045)

MySQL is up; `.env` password does not match **root** on your machine.

1. Open **MySQL Workbench** or `mysql -u root -p` and sign in with the password **you chose at install**.
2. Update repo `.env`:
   ```env
   DATABASE_URL=mysql+aiomysql://root:YOUR_PASSWORD@localhost:3306/tenderiq?charset=utf8mb4
   ```
   If the password contains `@`, encode it as `%40` (example: `TenderIQ@Dev123` → `TenderIQ%40Dev123`).

**Option A — set MySQL to match dev default** (if you want `TenderIQ@Dev123`):

```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'TenderIQ@Dev123';
FLUSH PRIVILEGES;
```

Then `.env`:
```env
DATABASE_URL=mysql+aiomysql://root:TenderIQ%40Dev123@localhost:3306/tenderiq?charset=utf8mb4
```

**Option B — keep your password:** only change `.env` to match what you already use.

---

## Deploy (Vercel + hosted API)

| Piece | Where |
|--------|--------|
| Web | Vercel — `NEXT_PUBLIC_API_URL` → your API URL |
| API | Railway / Render / Porter / similar |
| DB | Hosted MySQL (PlanetScale, Railway MySQL, Aiven free tier, etc.) |

Set `DATABASE_URL` on the API host to the provider’s MySQL URL. Do not use `localhost` in production.
