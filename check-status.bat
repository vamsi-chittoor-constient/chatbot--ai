@echo off
REM =============================================================================
REM Restaurant AI - Development Environment Status Checker
REM =============================================================================

echo.
echo ========================================
echo Restaurant AI - Service Status
echo ========================================
echo.

cd /d "%~dp0restaurant-chatbot"

echo Checking Docker containers...
echo.
docker compose ps
echo.

echo ----------------------------------------
echo.
echo Checking if services are responding:
echo.

echo [Docker - PostgreSQL]
docker compose exec -T postgres pg_isready -U admin -d restaurant_ai 2>nul && echo   Status: RUNNING || echo   Status: NOT RUNNING

echo.
echo [Docker - Redis]
docker compose exec -T redis redis-cli ping 2>nul && echo   Status: RUNNING || echo   Status: NOT RUNNING

echo.
echo [Docker - MongoDB]
docker compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping').ok" 2>nul && echo   Status: RUNNING || echo   Status: NOT RUNNING

echo.
echo [Backend API - Port 8000]
curl -s -o nul -w "  Status: %%{http_code}\n" http://localhost:8000/api/v1/health 2>nul || echo   Status: NOT RESPONDING

echo.
echo [Frontend - Port 5173]
curl -s -o nul -w "  Status: %%{http_code}\n" http://localhost:5173 2>nul || echo   Status: NOT RESPONDING

echo.
echo ========================================
echo.
pause
