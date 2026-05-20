@echo off
setlocal

echo ============================================================
echo   TenderIQ - Restarting Services
echo ============================================================
echo.

echo [1/3] Stopping existing services...
call "%~dp0..\run.bat" stop >nul 2>&1

echo [2/3] Waiting for ports to clear...
timeout /t 5 /nobreak >nul

echo [3/3] Starting services...
call "%~dp0..\run.bat"

pause