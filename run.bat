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

call :find_python
if errorlevel 1 (
    call :log "ERROR" "Python not found. Please install Python 3.10+ from python.org"
    exit /b 1
)

call :find_node
if errorlevel 1 (
    call :log "ERROR" "Node.js not found. Please install Node.js 18+ from nodejs.org"
    exit /b 1
)

call :check_postgres
if errorlevel 1 (
    call :log "WARN" "PostgreSQL not detected. You may need to install it manually."
)

call :check_redis
if errorlevel 1 (
    call :log "WARN" "Redis not detected. You may need to install it manually."
)

call :log "INFO" "System requirements check complete"
exit /b 0

:find_python
set PYTHON_BIN=
where python >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do call :log "INFO" "Found: %%i"
    set PYTHON_BIN=python
    exit /b 0
)
where python3 >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_BIN=python3
    exit /b 0
)
exit /b 1

:find_node
set NODE_BIN=
where node >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do call :log "INFO" "Found: %%i"
    set NODE_BIN=node
    exit /b 0
)
exit /b 1

:check_postgres
where psql >nul 2>&1
if %errorlevel%==0 (
    call :log "INFO" "PostgreSQL client found"
    exit /b 0
)
exit /b 1

:check_redis
where redis-cli >nul 2>&1
if %errorlevel%==0 (
    call :log "INFO" "Redis client found"
    exit /b 0
)
exit /b 1

:: ============================================
:: DEPENDENCY CHECK AND INSTALL
:: ============================================
:check_dependencies
call :log "INFO" "Checking dependencies..."

if not exist "%BACKEND_DIR%\venv" (
    call :log "INFO" "Creating Python virtual environment..."
    cd /d "%BACKEND_DIR%"
    python -m venv venv
    if errorlevel 1 (
        call :log "ERROR" "Failed to create virtual environment"
        exit /b 1
    )
)

call :install_backend_deps
if errorlevel 1 exit /b 1

call :install_frontend_deps
if errorlevel 1 exit /b 1

call :log "INFO" "Dependencies installed successfully"
exit /b 0

:install_backend_deps
cd /d "%BACKEND_DIR%"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    if exist requirements.txt (
        pip install -r requirements.txt --quiet
        if errorlevel 1 (
            call :log "ERROR" "Failed to install backend requirements"
            exit /b 1
        )
    )
    call :log "INFO" "Backend dependencies installed"
) else (
    call :log "ERROR" "Virtual environment not found"
    exit /b 1
)
deactivate
exit /b 0

:install_frontend_deps
cd /d "%FRONTEND_DIR%"
if exist package.json (
    call npm install --silent
    if errorlevel 1 (
        call :log "ERROR" "Failed to install frontend dependencies"
        exit /b 1
    )
    call :log "INFO" "Frontend dependencies installed"
) else (
    call :log "ERROR" "package.json not found"
    exit /b 1
)
exit /b 0

:: ============================================
:: ENVIRONMENT SETUP
:: ============================================
:setup_environment
call :log "INFO" "Setting up environment..."

if not exist "%SCRIPT_DIR%data" mkdir "%SCRIPT_DIR%data"
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"
if not exist "%SCRIPT_DIR%uploads" mkdir "%SCRIPT_DIR%uploads"

if not exist "%ENV_FILE%" (
    call :log "INFO" "Creating default .env file..."
    call :create_default_env
)

call :log "INFO" "Environment setup complete"
exit /b 0

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
exit /b 0

:: ============================================
:: BACKEND SETUP
:: ============================================
:setup_backend
call :log "INFO" "Setting up backend..."

cd /d "%BACKEND_DIR%"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    python -c "import sys; print('Python OK')" >nul 2>&1
    call :log "INFO" "Backend setup complete"
    deactivate
) else (
    call :log "WARN" "Virtual environment not found - skipping backend setup"
)
exit /b 0

:: ============================================
:: FRONTEND SETUP
:: ============================================
:setup_frontend
call :log "INFO" "Setting up frontend..."

cd /d "%FRONTEND_DIR%"
if exist package.json (
    call :log "INFO" "Frontend setup complete"
) else (
    call :log "WARN" "Frontend package.json not found"
)
exit /b 0

:: ============================================
:: START SERVICES
:: ============================================
:start_services
call :log "INFO" "Starting all services..."

cd /d "%BACKEND_DIR%"
if exist venv\Scripts\activate.bat (
    start /b cmd /c "call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    call :log "INFO" "Backend starting on http://localhost:8000"
) else (
    call :log "ERROR" "Cannot start backend - venv not found"
)

cd /d "%FRONTEND_DIR%"
start /b cmd /c "npm run dev"
call :log "INFO" "Frontend starting on http://localhost:3000"

exit /b 0

:: ============================================
:: HEALTH CHECK
:: ============================================
:health_check
timeout /t 5 /nobreak >nul

curl -s -o nul -w "%%{http_code}" http://localhost:8000/health 2>nul | findstr "200" >nul
if %errorlevel%==0 (
    call :log "INFO" "[OK] Backend API is healthy"
    exit /b 0
)
call :log "WARN" "[WARN] Backend not ready yet"
exit /b 1

:: ============================================
:: MAIN EXECUTION FLOW
:: ============================================

echo.
echo ============================================================
echo   TenderIQ SaaS Platform - One-Click Startup
echo ============================================================
echo.

call :log "INFO" "Starting TenderIQ startup sequence..."

call :check_system_requirements
if errorlevel 1 (
    echo.
    echo %RED%[ERROR]%RESET% Startup failed. Check logs at: %LOG_FILE%
    echo.
    pause
    exit /b 1
)

call :check_dependencies
if errorlevel 1 (
    echo.
    echo %RED%[ERROR]%RESET% Startup failed. Check logs at: %LOG_FILE%
    echo.
    pause
    exit /b 1
)

call :setup_environment
call :setup_backend
call :setup_frontend
call :start_services
call :health_check

echo.
echo ============================================================
echo %GREEN%[SUCCESS]%RESET% TenderIQ Started!
echo ============================================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   Docs:     http://localhost:8000/docs
echo.
echo Press any key to open browser...
pause >nul

start http://localhost:3000

endlocal
exit /b 0