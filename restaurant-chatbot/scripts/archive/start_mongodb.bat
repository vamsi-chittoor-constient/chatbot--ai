@echo off
REM Start MongoDB Server
echo ========================================
echo Starting MongoDB Server
echo ========================================
echo.

cd /d "%~dp0"

REM Create data directory if it doesn't exist
if not exist "data\mongodb" mkdir data\mongodb

.\mongodb\mongod.exe --dbpath data\mongodb --port 27017 --bind_ip localhost --logpath data\mongodb\mongo.log

pause
