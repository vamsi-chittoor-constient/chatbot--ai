@echo off
REM =============================================================================
REM Restaurant AI - Development Environment Launcher
REM =============================================================================
REM This script launches all components in separate windows for debugging:
REM - Docker containers (PostgreSQL, Redis, MongoDB)
REM - Backend API (FastAPI)
REM - Frontend (React/Vite)
REM =============================================================================

echo.
echo ========================================
echo Restaurant AI - Starting Development
echo ========================================
echo.

cd /d "%~dp0restaurant-chatbot"

REM Check if we're in the right directory
if not exist "docker-compose.yml" (
    echo ERROR: docker-compose.yml not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

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

echo All dependencies found!
echo.

echo [1/3] Starting Docker containers (PostgreSQL, Redis, MongoDB, PetPooja)...
start "Docker - Database Containers" cmd /k "cd /d "%~dp0restaurant-chatbot" && docker compose up postgres redis mongodb petpooja-service"

REM Wait a bit for databases to start initializing
timeout /t 5 /nobreak >nul

echo [2/3] Starting Backend API (FastAPI on port 8000)...
start "Backend - FastAPI" cmd /k "cd /d "%~dp0restaurant-chatbot" && python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to be ready before starting frontend
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
echo [3/3] Starting Frontend (Vite on port 3000)...
start "Frontend - Vite Dev Server" cmd /k "cd /d "%~dp0restaurant-chatbot\frontend" && npm run dev"

echo.
echo ========================================
echo All components launched!
echo ========================================
echo.
echo Docker Containers: PostgreSQL (5433), Redis (6379), MongoDB (27017), PetPooja (8001)
echo Backend API:       http://localhost:8000
echo Frontend:          http://localhost:3000
echo PetPooja Service:  http://localhost:8001
echo API Docs:          http://localhost:8000/docs
echo.
echo Check the separate windows for logs and debugging.
echo Press any key to exit this launcher window...
pause >nul
