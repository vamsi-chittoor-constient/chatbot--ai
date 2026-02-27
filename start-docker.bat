@echo off
REM =============================================================================
REM Start Docker Containers Only
REM =============================================================================
REM Starts: PostgreSQL, Redis, MongoDB
REM After this completes, run start-local.bat to start backend and frontend
REM =============================================================================

echo.
echo ========================================
echo Starting Docker Containers
echo ========================================
echo.

cd /d "%~dp0restaurant-chatbot"

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Starting containers: PostgreSQL, Redis, MongoDB...
echo.

docker compose up -d postgres redis mongodb

echo.
echo Waiting for containers to be healthy...
timeout /t 5 /nobreak >nul

REM Check container status
docker ps --filter "name=restaurant-postgres" --filter "name=restaurant-redis" --filter "name=restaurant-mongodb" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo ========================================
echo Docker Containers Started!
echo ========================================
echo.
echo PostgreSQL:        localhost:5433
echo Redis:             localhost:6379
echo MongoDB:           localhost:27017
echo.
echo Status: docker ps
echo Logs:   docker compose logs -f
echo Stop:   stop-dev.bat
echo.
echo Next step: Run start-local.bat to start backend and frontend
echo.
pause
