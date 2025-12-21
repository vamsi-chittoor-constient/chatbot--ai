@echo off
REM Start Frontend Development Server
echo ========================================
echo Starting Frontend (Vite)
echo ========================================
echo.

cd /d "%~dp0\test_frontend"
npm run dev

pause
