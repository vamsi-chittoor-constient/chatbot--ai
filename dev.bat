@echo off
REM Quick Dev Startup - Kills existing processes and starts fresh
echo ========================================
echo Restaurant AI - Dev Server Startup
echo ========================================

REM Kill any existing processes on ports 3000 and 8000
echo.
echo [INFO] Cleaning up ports...
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

REM Start backend in new window
echo [INFO] Starting Backend API on port 8000...
start "Backend API" cmd /k "cd /d %~dp0restaurant-chatbot && call venv\Scripts\activate && uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to be healthy (poll /health endpoint)
echo [INFO] Waiting for backend to be healthy...
set MAX_ATTEMPTS=60
set ATTEMPT=0

:check_health
set /a ATTEMPT+=1
if %ATTEMPT% gtr %MAX_ATTEMPTS% (
    echo [ERROR] Backend failed to start after %MAX_ATTEMPTS% attempts
    echo [INFO] Starting frontend anyway...
    goto start_frontend
)

REM Try to reach the backend health endpoint using curl.exe (native Windows 10+)
curl.exe -s -o nul -w "%%{http_code}" http://localhost:8000/api/v1/health/quick 2>nul | findstr "200" >nul
if errorlevel 1 (
    echo     Attempt %ATTEMPT%/%MAX_ATTEMPTS% - Backend not ready yet...
    timeout /t 2 /nobreak >nul
    goto check_health
)

echo [OK] Backend is healthy!
echo.

:start_frontend
REM Start frontend in new window
echo [INFO] Starting Frontend on port 3000...
start "Frontend" cmd /k "cd /d %~dp0restaurant-chatbot\frontend && npm run dev"

echo.
echo ========================================
echo Dev servers starting!
echo ========================================
echo.
echo - Backend:  http://localhost:8000
echo - Frontend: http://localhost:3000
echo.
echo Check the command windows for status.
echo.
