@echo off
REM Stop All Services
echo ========================================
echo Stopping All Services
echo ========================================
echo.
echo This will stop:
echo - Backend API (Python)
echo - Frontend Dev Server (Node.js)
echo - Redis Server
echo - MongoDB Server
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

echo.
echo [INFO] Stopping Backend API (Python)...
taskkill /F /IM python.exe 2>nul
if errorlevel 1 (
    echo [WARN] No Python processes found
) else (
    echo [OK] Python processes terminated
)

echo.
echo [INFO] Stopping Frontend Dev Server (Node.js)...
taskkill /F /IM node.exe 2>nul
if errorlevel 1 (
    echo [WARN] No Node.js processes found
) else (
    echo [OK] Node.js processes terminated
)

echo.
echo [INFO] Stopping Redis Server...
taskkill /F /IM redis-server.exe 2>nul
if errorlevel 1 (
    echo [WARN] No Redis processes found
) else (
    echo [OK] Redis server terminated
)

echo.
echo [INFO] Stopping MongoDB Server...
taskkill /F /IM mongod.exe 2>nul
if errorlevel 1 (
    echo [WARN] No MongoDB processes found
) else (
    echo [OK] MongoDB server terminated
)

echo.
echo ========================================
echo All Services Stopped
echo ========================================
echo.
pause
