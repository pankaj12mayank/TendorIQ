@echo off
echo Stopping TenderIQ...
call "%~dp0run.bat" stop 2>nul
echo Deleting Next.js cache...
rmdir /s /q "%~dp0web\.next" 2>nul
echo Done. Now run run.bat
pause

