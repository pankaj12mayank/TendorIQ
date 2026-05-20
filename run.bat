@echo off
setlocal EnableDelayedExpansion
title TenderIQ - Starting

set "ROOT=%~dp0"
cd /d "%ROOT%"
set "TENDERIQ_FORCE_SETUP=0"

echo.
echo  TenderIQ - One-click startup (no Docker required)
echo  ==================================================
echo.

if /I "%~1"=="stop" goto :do_stop
if /I "%~1"=="setup" goto :do_setup
if /I "%~1"=="full" goto :do_setup

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
echo To stop servers, run: run.bat stop
echo To force full dependency setup, run: run.bat setup
pause >nul
exit /b 0

:do_setup
set "TENDERIQ_FORCE_SETUP=1"
echo [INFO] Full setup mode enabled (dependency reinstall/check forced).
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\tenderiq-start.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Startup failed in setup mode. See .tenderiq\startup.log
    pause
    exit /b %EXIT_CODE%
)
echo.
echo Opening http://localhost:3000 in your browser...
timeout /t 3 /nobreak >nul
start "" "http://localhost:3000"
echo.
echo Press any key to close this window (servers keep running in background).
echo To stop servers, run: run.bat stop
pause >nul
exit /b 0

:do_stop
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\tenderiq-stop.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] Stop failed.
    pause
    exit /b %EXIT_CODE%
)
echo.
echo TenderIQ services stopped.
exit /b 0
