@echo off
setlocal

echo ============================================================
echo   TenderIQ - Stopping All Services
echo ============================================================
echo.

:: Kill Node.js processes (frontend)
echo [1/4] Stopping frontend...
taskkill /f /im node.exe /fi "windowtitle eq *next*" 2>nul
taskkill /f /im npm.exe 2>nul

:: Kill Python processes (backend)
echo [2/4] Stopping backend...
taskkill /f /im python.exe /fi "windowtitle eq *uvicorn*" 2>nul
taskkill /f /im python.exe /fi "windowtitle eq *tenderiq*" 2>nul

:: Kill Redis if running as daemon
echo [3/4] Stopping Redis...
taskkill /f /im redis-server.exe 2>nul

:: Clean up
echo [4/4] Cleaning up...
if exist "%~dp0.pid" del "%~dp0.pid"

echo.
echo %GREEN%[OK]%RESET% All services stopped.
echo.
pause