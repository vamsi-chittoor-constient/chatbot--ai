@echo off
REM Start Redis Server
echo ========================================
echo Starting Redis Server
echo ========================================
echo.

cd /d "%~dp0"
.\redis\redis-server.exe --port 6379 --save "" --appendonly no

pause
