@echo off
setlocal EnableDelayedExpansion
title TenderIQ - Starting

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo  TenderIQ - One-click startup (no Docker required)
echo  ==================================================
echo.

where powershell >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PowerShell is required.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\tenderiq-start.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Startup failed. See .tenderiq\startup.log
    pause
    exit /b %EXIT_CODE%
)

echo.
echo Opening http://localhost:3000 in your browser...
timeout /t 3 /nobreak >nul
start "" "http://localhost:3000"

echo.
echo Press any key to close this window (servers keep running in background).
echo To stop servers, run stop.bat
pause >nul
exit /b 0
