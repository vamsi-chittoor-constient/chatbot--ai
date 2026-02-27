@echo off
REM =============================================================================
REM Restaurant AI - Stop Development Environment
REM =============================================================================
REM This script stops all Docker containers gracefully
REM =============================================================================

echo.
echo ========================================
echo Restaurant AI - Stopping Development
echo ========================================
echo.

cd /d "%~dp0restaurant-chatbot"

echo Stopping Docker containers...
docker compose down

echo.
echo ========================================
echo Docker containers stopped!
echo ========================================
echo.
echo Note: Backend and Frontend windows need to be closed manually
echo       or press Ctrl+C in each window to stop them.
echo.
pause
