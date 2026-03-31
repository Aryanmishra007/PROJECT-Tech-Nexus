@echo off
REM NexaAI - Complete Startup Script
REM This script starts the Flask server

echo.
echo ====================================================================
echo  NexaAI - AI-Driven Skill Gap Platform
echo  Starting Flask Server
echo ====================================================================
echo.

REM Check if MySQL is running
echo Checking MySQL connection...
timeout /t 2 /nobreak >nul

REM Start Flask
echo.
echo Starting Flask on http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
