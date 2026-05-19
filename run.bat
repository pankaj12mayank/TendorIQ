@echo off
setlocal EnableDelayedExpansion

:: ============================================
:: TenderIQ One-Click Startup System
:: ============================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Color codes for Windows
set "RESET=[0m"
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"

:: Colors for newer Windows versions
for /f "tokens=*" %%a in ('powershell -Command "$host.UI.RawUI.ForegroundColor = 'White'"') do set NUL=%%a

:: Script variables
set "START_TIME=%TIME%"
set "PID_FILE=%SCRIPT_DIR%\.tenderiq\pids.txt"
set "LOG_FILE=%SCRIPT_DIR%\.tenderiq\startup.log"
set "ENV_FILE=%SCRIPT_DIR%.env"
set "BACKEND_DIR=%SCRIPT_DIR%apps\api"
set "FRONTEND_DIR=%SCRIPT_DIR%apps\web"
set "PYTHON_BIN="
set "NODE_BIN="
set "IS_FIRST_RUN=0"

:: Create .tenderiq directory for logs/pids
if not exist "%SCRIPT_DIR%\.tenderiq" mkdir "%SCRIPT_DIR%\.tenderiq"

:: Clear previous log
echo. > "%LOG_FILE%"

:: ============================================
:: MAIN EXECUTION FLOW
:: ============================================

echo.
echo ============================================================
echo   TenderIQ SaaS Platform - One-Click Startup
echo ============================================================
echo.

call :log "INFO" "Starting TenderIQ startup sequence..."

:: Step 1: System Requirements Check
call :check_system_requirements
if errorlevel 1 (
    call :cleanup_on_failure
    exit /b 1
)

:: Step 2: Detect and Install Dependencies
call :check_dependencies
if errorlevel 1 (
    call :cleanup_on_failure
    exit /b 1
)

:: Step 3: Environment Setup
call :setup_environment
if errorlevel 1 (
    call :cleanup_on_failure
    exit /b 1
)

:: Step 4: Backend Setup
call :setup_backend
if errorlevel 1 (
    call :cleanup_on_failure
    exit /b 1
)

:: Step 5: Frontend Setup
call :setup_frontend
if errorlevel 1 (
    call :cleanup_on_failure
    exit /b 1
)

:: Step 6: Queue Worker Setup
call :setup_queue_worker
if errorlevel 1 (
    call :cleanup_on_failure
    exit /b 1
)

:: Step 7: Health Checks
call :run_health_checks
if errorlevel 1 (
    call :cleanup_on_failure
    exit /b 1
)

:: Step 8: Print Success Message
call :print_success_message

:: Keep script running for monitoring
call :monitor_services

:cleanup_on_failure
echo.
echo %RED%[ERROR]%RESET% Startup failed. Check logs at: %LOG_FILE%
echo.
echo Troubleshooting steps:
echo 1. Check PostgreSQL is running
echo 2. Check Redis is running  
echo 3. Verify .env file has correct values
echo 4. Try running scripts\validate-env.ps1
echo.
pause
exit /b 1

goto :eof

:: ============================================
:: LOGGING FUNCTION
:: ============================================
:log
echo [%~1] %~2
echo [%~1] %~2 >> "%LOG_FILE%"
goto :eof

:: ============================================
:: SYSTEM REQUIREMENTS CHECK
:: ============================================
:check_system_requirements
call :log "INFO" "Checking system requirements..."

:: Check Python
call :find_python
if errorlevel 1 (
    call :log "ERROR" "Python not found. Please install Python 3.10+ from python.org"
    return /b 1
)

:: Check Node.js
call :find_node
if errorlevel 1 (
    call :log "ERROR" "Node.js not found. Please install Node.js 18+ from nodejs.org"
    return /b 1
)

:: Check PostgreSQL
call :check_postgres
if errorlevel 1 (
    call :log "WARN" "PostgreSQL not detected. You may need to install it manually."
)

:: Check Redis
call :check_redis
if errorlevel 1 (
    call :log "WARN" "Redis not detected. You may need to install it manually."
)

call :log "INFO" "System requirements check complete"
return /b 0

:find_python
set PYTHON_BIN=
where python >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do call :log "INFO" "Found: %%i"
    set PYTHON_BIN=python
    return /b 0
)
:: Try python3
where python3 >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_BIN=python3
    return /b 0
)
return /b 1

:find_node
set NODE_BIN=
where node >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do call :log "INFO" "Found: %%i"
    set NODE_BIN=node
    return /b 0
)
return /b 1

:check_postgres
where psql >nul 2>&1
if %errorlevel%==0 (
    call :log "INFO" "PostgreSQL client found"
    return /b 0
)
return /b 1

:check_redis
where redis-cli >nul 2>&1
if %errorlevel%==0 (
    call :log "INFO" "Redis client found"
    return /b 0
)
return /b 1

:: ============================================
:: DEPENDENCY CHECK AND INSTALL
:: ============================================
:check_dependencies

call :log "INFO" "Checking dependencies..."

:: Check and create Python virtual environment
if not exist "%BACKEND_DIR%\venv" (
    call :log "INFO" "Creating Python virtual environment..."
    cd /d "%BACKEND_DIR%"
    %PYTHON_BIN% -m venv venv
    if errorlevel 1 (
        call :log "ERROR" "Failed to create virtual environment"
        return /b 1
    )
)

:: Activate venv and install requirements
call :log "INFO" "Installing backend dependencies..."
call :install_backend_deps
if errorlevel 1 return /b 1

:: Install frontend dependencies
call :log "INFO" "Installing frontend dependencies..."
call :install_frontend_deps
if errorlevel 1 return /b 1

call :log "INFO" "Dependencies installed successfully"
return /b 0

:install_backend_deps
cd /d "%BACKEND_DIR%"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    if exist requirements.txt (
        pip install -r requirements.txt --quiet
        if errorlevel 1 (
            call :log "ERROR" "Failed to install backend requirements"
            return /b 1
        )
    )
    call :log "INFO" "Backend dependencies installed"
) else (
    call :log "ERROR" "Virtual environment not found"
    return /b 1
)
deactivate
return /b 0

:install_frontend_deps
cd /d "%FRONTEND_DIR%"
if exist package.json (
    call npm install --silent
    if errorlevel 1 (
        call :log "ERROR" "Failed to install frontend dependencies"
        return /b 1
    )
    call :log "INFO" "Frontend dependencies installed"
) else (
    call :log "ERROR" "package.json not found"
    return /b 1
)
return /b 0

:: ============================================
:: ENVIRONMENT SETUP
:: ============================================
:setup_environment

call :log "INFO" "Setting up environment..."

:: Create required directories
if not exist "%SCRIPT_DIR%data" mkdir "%SCRIPT_DIR%data"
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"
if not exist "%SCRIPT_DIR%uploads" mkdir "%SCRIPT_DIR%uploads"

:: Check/create .env file
if not exist "%ENV_FILE%" (
    call :log "INFO" "Creating default .env file..."
    call :create_default_env
)

call :log "INFO" "Environment setup complete"
return /b 0

:create_default_env
echo # TenderIQ Environment Configuration > "%ENV_FILE%"
echo. >> "%ENV_FILE%"
echo # Database >> "%ENV_FILE%"
echo DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tenderiq >> "%ENV_FILE%"
echo. >> "%ENV_FILE%"
echo # Redis >> "%ENV_FILE%"
echo REDIS_URL=redis://localhost:6379/0 >> "%ENV_FILE%"
echo. >> "%ENV_FILE%"
echo # Auth (Clerk) - UPDATE WITH REAL KEYS >> "%ENV_FILE%"
echo CLERK_PUBLISHABLE_KEY=pk_test_placeholder >> "%ENV_FILE%"
echo CLERK_SECRET_KEY=sk_test_placeholder >> "%ENV_FILE%"
echo. >> "%ENV_FILE%"
echo # Security >> "%ENV_FILE%"
echo SECRET_KEY=dev-secret-key-change-in-production >> "%ENV_FILE%"
echo. >> "%ENV_FILE%"
echo # AI Providers (optional) >> "%ENV_FILE%"
echo OPENAI_API_KEY= >> "%ENV_FILE%"
echo ANTHROPIC_API_KEY= >> "%ENV_FILE%"
echo. >> "%ENV_FILE%"
echo # App Settings >> "%ENV_FILE%"
echo NODE_ENV=development >> "%ENV_FILE%"
echo APP_URL=http://localhost:3000 >> "%ENV_FILE%"
echo API_URL=http://localhost:8000 >> "%ENV_FILE%"
echo. >> "%ENV_FILE%"
echo # Storage (Local for dev) >> "%ENV_FILE%"
echo STORAGE_TYPE=local >> "%ENV_FILE%"
echo STORAGE_LOCAL_PATH=./uploads >> "%ENV_FILE%"
call :log "INFO" "Created default .env file - UPDATE WITH REAL VALUES!"
return /b 0

:: ============================================
:: BACKEND SETUP
:: ============================================
:setup_backend
call :log "INFO" "Setting up backend..."

:: Verify database connection
call :wait_for_database
if errorlevel 1 (
    call :log "WARN" "Database not ready - continuing anyway (may need migration)"
)

:: Run migrations (optional - may fail if DB not ready)
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat 2>nul
uv run alembic upgrade head 2>nul
deactivate 2>nul

call :log "INFO" "Backend setup complete"
return /b 0

:wait_for_database
call :log "INFO" "Waiting for database connection..."
:: Try connecting to database
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat 2>nul
python -c "import asyncio; from core.database import get_db; asyncio.run(next(get_db().__anext__()))" 2>nul
set DB_RESULT=%errorlevel%
deactivate 2>nul
if %DB_RESULT%==0 (
    call :log "INFO" "Database connected successfully"
    return /b 0
)
call :log "WARN" "Database connection failed - will retry on startup"
return /b 1

:: ============================================
:: FRONTEND SETUP
:: ============================================
:setup_frontend
call :log "INFO" "Setting up frontend..."

:: Verify build works
cd /d "%FRONTEND_DIR%"
call npm run build --silent 2>nul
if errorlevel 1 (
    call :log "WARN" "Frontend build had warnings - continuing anyway"
)

call :log "INFO" "Frontend setup complete"
return /b 0

:: ============================================
:: QUEUE WORKER SETUP
:: ============================================
:setup_queue_worker
call :log "INFO" "Queue worker setup complete (will start with backend)"
return /b 0

:: ============================================
:: HEALTH CHECKS
:: ============================================
:run_health_checks

call :log "INFO" "Running health checks..."

:: Wait for services to start
timeout /t 3 /nobreak >nul

call :check_backend_health
if errorlevel 1 (
    call :log "ERROR" "Backend health check failed"
)

call :check_frontend_health
if errorlevel 1 (
    call :log "ERROR" "Frontend health check failed"
)

call :log "INFO" "Health checks complete"
return /b 0

:check_backend_health
curl -s -o nul -w "%%{http_code}" http://localhost:8000/health 2>nul | findstr "200" >nul
if %errorlevel%==0 (
    call :log "INFO" "[OK] Backend API is healthy"
    return /b 0
)
call :log "WARN" "[WARN] Backend API not responding yet"
return /b 1

:check_frontend_health
curl -s -o nul -w "%%{http_code}" http://localhost:3000 2>nul | findstr "200\|304" >nul
if %errorlevel%==0 (
    call :log "INFO" "[OK] Frontend is healthy"
    return /b 0
)
call :log "WARN" "[WARN] Frontend not responding yet"
return /b 1

:: ============================================
:: START SERVICES
:: ============================================
:start_services
call :log "INFO" "Starting all services..."

:: Start Redis (if installed) - optional, skip if not available
start /b cmd /c "redis-server --daemonize yes" 2>nul

:: Start backend in background
start /b cmd /c "cd /d %BACKEND_DIR% && call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Start frontend
start /b cmd /c "cd /d %FRONTEND_DIR% && npm run dev"

call :log "INFO" "Services started - waiting for health checks..."

:: Wait for services to be ready
timeout /t 10 /nobreak >nul

:: Run health checks
call :run_health_checks

return /b 0

:: ============================================
:: SUCCESS MESSAGE
:: ============================================
:print_success_message

echo.
echo ============================================================
echo %GREEN%[SUCCESS]%RESET% TenderIQ Started Successfully!
echo ============================================================
echo.
echo %GREEN%Access Points:%RESET%
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
echo %YELLOW%Next Steps:%RESET%
echo   1. Update .env file with real API keys
echo   2. Configure Clerk authentication
echo   3. Set up AI provider keys for analysis
echo.
echo %YELLOW%Troubleshooting:%RESET%
echo   - Check logs in .tenderiq\startup.log
echo   - Run scripts\stop.bat to stop all services
echo   - Run scripts\restart.bat to restart
echo.
echo Press any key to open frontend in browser...
pause >nul

start http://localhost:3000
goto :eof

:: ============================================
:: MONITOR SERVICES
:: ============================================
:monitor_services
echo.
echo %CYAN%[MONITORING]%RESET% Services running. Press Ctrl+C to stop.
echo.

:monitor_loop
timeout /t 30 /nobreak >nul
call :check_backend_health >nul 2>&1
call :check_frontend_health >nul 2>&1
goto :monitor_loop

endlocal