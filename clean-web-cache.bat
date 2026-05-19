@echo off
echo Stopping TenderIQ...
call "%~dp0stop.bat" 2>nul
echo Deleting Next.js cache...
rmdir /s /q "%~dp0apps\web\.next" 2>nul
echo Done. Now run run.bat
pause
