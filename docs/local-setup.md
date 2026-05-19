# TenderIQ Local Setup Guide

## Quick Start (One-Click)

The easiest way to run TenderIQ locally is to use the one-click startup system:

### Prerequisites (Required)

Before running TenderIQ, you need to install:

1. **Python 3.10+** - Download from https://www.python.org/downloads/
2. **Node.js 18+** - Download from https://nodejs.org/
3. **PostgreSQL 15+** - Download from https://www.postgresql.org/download/windows/
4. **Redis** - Download from https://redis.io/download (or use Redis Windows port)

### Quick Start Steps

```batch
1. Clone or download the TenderIQ project
2. Double-click run.bat
3. Wait for automatic installation and startup
4. Open http://localhost:3000 in your browser
```

That's it! The system will automatically:
- Check for required software
- Create Python virtual environment
- Install all dependencies
- Create default configuration
- Start all services
- Verify everything is working

---

## Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/tenderiq.git
cd tenderiq
```

### 2. Backend Setup

```bash
cd apps/api

# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy ..\..\.env.example .env
# Edit .env with your settings
```

### 3. Frontend Setup

```bash
cd apps/web

# Install dependencies
npm install
```

### 4. Start Services

```bash
# Terminal 1 - Start Redis (if not running)
redis-server

# Terminal 2 - Backend
cd apps/api
venv\Scripts\activate
uvicorn main:app --reload

# Terminal 3 - Frontend  
cd apps/web
npm run dev
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/tenderiq

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication (Clerk) - Get from https://clerk.com
CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# Security (Generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your-generated-secret-key

# AI Providers (Optional) - Get from https://platform.openai.com
OPENAI_API_KEY=sk-xxx

# App URLs
NODE_ENV=development
APP_URL=http://localhost:3000
API_URL=http://localhost:8000
```

---

## Troubleshooting

### "Python not found"

Install Python from https://www.python.org/downloads/
Make sure to check "Add Python to PATH" during installation.

### "Node.js not found"

Install Node.js from https://nodejs.org/
Use version 18 or higher.

### "PostgreSQL connection failed"

1. Start PostgreSQL service:
   - Windows: Start "PostgreSQL" service from Services app
   - Or run: `pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start`

2. Create database:
   ```bash
   createdb tenderiq
   ```

### "Redis connection failed"

1. Install Redis for Windows or use WSL
2. Or install Memurai/Redis Windows port
3. Start Redis: `redis-server`

### "Port already in use"

Stop other services using the port:
```batch
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### "Module not found"

Reinstall dependencies:
```batch
cd apps/api
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `run.bat` | One-click startup (main script) |
| `scripts/stop.bat` | Stop all services |
| `scripts/restart.bat` | Restart all services |
| `scripts/validate-env.ps1` | Validate environment |
| `scripts/health-check.ps1` | Check service health |

---

## Services

When running, TenderIQ starts these services:

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Next.js web app |
| Backend API | 8000 | FastAPI server |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Queue/Cache |

---

## Access Points

After successful startup:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Support

For issues:
1. Check the logs in `.tenderiq/startup.log`
2. Run `scripts/validate-env.ps1`
3. Run `scripts/health-check.ps1`
4. Check the troubleshooting section above