@echo off
REM Quick Stop - Kills processes on dev ports
echo ========================================
echo Restaurant AI - Stop Dev Servers
echo ========================================
echo.

echo [INFO] Killing processes on port 8000 (Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    echo Killing PID %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo [INFO] Killing processes on port 3000 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
    echo Killing PID %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo [OK] Dev servers stopped
echo.
