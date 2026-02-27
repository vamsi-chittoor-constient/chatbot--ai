@echo off
REM Start Backend API Server
echo ========================================
echo Starting Backend API Server
echo ========================================
echo.

cd /d "%~dp0"
python start_services.py

pause
