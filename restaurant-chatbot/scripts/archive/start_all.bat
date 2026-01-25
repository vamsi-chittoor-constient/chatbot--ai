@echo off
REM Start All Services in Separate Windows
echo ========================================
echo Starting All Services
echo ========================================
echo.
echo This will open 4 separate windows for:
echo 1. Redis Server
echo 2. MongoDB Server
echo 3. Backend API
echo 4. Frontend Dev Server
echo.
echo Press any key to continue...
pause > nul

cd /d "%~dp0"

REM Kill any existing processes on ports 3000 and 8000
echo.
echo [INFO] Cleaning up ports 3000 and 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    echo Killing process on port 8000 ^(PID %%a^)
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
    echo Killing process on port 3000 ^(PID %%a^)
    taskkill /F /PID %%a 2>nul
)
echo [OK] Ports cleaned up
echo.

REM Start Redis in new window
start "Redis Server" cmd /k start_redis.bat

REM Wait 2 seconds
timeout /t 2 /nobreak > nul

REM Start MongoDB in new window
start "MongoDB Server" cmd /k start_mongodb.bat

REM Wait 3 seconds for MongoDB to initialize
timeout /t 3 /nobreak > nul

REM Start Backend in new window
start "Backend API" cmd /k start_backend.bat

REM Wait 2 seconds
timeout /t 2 /nobreak > nul

REM Start Frontend in new window
start "Frontend Dev Server" cmd /k start_frontend.bat

echo.
echo ========================================
echo All services are starting!
echo ========================================
echo.
echo Check the 4 command windows for status.
echo.
echo Services:
echo - Redis:    localhost:6379
echo - MongoDB:  localhost:27017
echo - Backend:  http://localhost:8000
echo - Frontend: http://localhost:3000
echo.
echo To stop all services: Close all 4 windows or press Ctrl+C in each
echo.
pause
