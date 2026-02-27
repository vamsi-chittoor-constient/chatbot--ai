@echo off
REM =============================================================================
REM Start Backend and Frontend Locally
REM =============================================================================
REM IMPORTANT: Run start-docker.bat FIRST to start Docker containers
REM This script starts backend and frontend with smart startup sequencing
REM =============================================================================

echo.
echo ========================================
echo Starting Local Development Services
echo ========================================
echo.

cd /d "%~dp0restaurant-chatbot"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH!
    pause
    exit /b 1
)

REM Check if Docker containers are running
docker ps --filter "name=restaurant-postgres" --format "{{.Names}}" | findstr "restaurant-postgres" >nul
if errorlevel 1 (
    echo ERROR: Docker containers are not running!
    echo Please run start-docker.bat first.
    pause
    exit /b 1
)

echo All dependencies found!
echo.

echo [1/2] Starting Backend API (FastAPI on port 8000)...
start "Backend - FastAPI" cmd /k "cd /d "%~dp0restaurant-chatbot" && python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to be ready before starting frontend
echo.
echo Waiting for backend to be ready...
set MAX_RETRIES=60
set RETRY_COUNT=0

:WAIT_BACKEND
set /a RETRY_COUNT+=1
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if %errorlevel% equ 0 (
    echo Backend is ready!
    goto BACKEND_READY
)
if %RETRY_COUNT% geq %MAX_RETRIES% (
    echo WARNING: Backend health check timed out after 60 seconds
    echo Starting frontend anyway...
    goto BACKEND_READY
)
timeout /t 1 /nobreak >nul
goto WAIT_BACKEND

:BACKEND_READY
echo.
echo [2/2] Starting Frontend (Vite on port 3000)...
start "Frontend - Vite Dev Server" cmd /k "cd /d "%~dp0restaurant-chatbot\frontend" && npm run dev"

echo.
echo ========================================
echo Local Services Started!
echo ========================================
echo.
echo Backend API:       http://localhost:8000
echo Frontend:          http://localhost:3000
echo API Docs:          http://localhost:8000/docs
echo.
echo Check the separate windows for logs.
echo Press any key to exit this launcher window...
pause >nul
