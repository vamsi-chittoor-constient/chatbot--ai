@echo off
REM =============================================================================
REM Restaurant AI - Restart Development Environment
REM =============================================================================
REM This script stops Docker containers and relaunches everything
REM =============================================================================

echo.
echo ========================================
echo Restaurant AI - Restarting Development
echo ========================================
echo.

cd /d "%~dp0restaurant-chatbot"

echo Stopping Docker containers...
docker compose down

echo.
echo Waiting for cleanup...
timeout /t 3 /nobreak >nul

echo Restarting all services...
cd ..
call run-dev.bat
