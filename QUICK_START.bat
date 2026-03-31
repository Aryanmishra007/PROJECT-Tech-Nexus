@echo off
color 0A
title ResumeAI - Complete Setup

echo.
echo ████████████████████████████████████████████████████████
echo █                                                      █
echo █          ResumeAI - Career Intelligence Platform    █
echo █                 Complete Setup Script               █
echo █                                                      █
echo ████████████████████████████████████████████████████████
echo.

echo ========================================================
echo STEP 1: Installing Python Dependencies
echo ========================================================
echo.

python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing required packages...
echo.

pip install flask==3.0.0 --quiet
pip install flask-cors==4.0.0 --quiet
pip install werkzeug==3.0.1 --quiet
pip install PyPDF2==3.0.1 --quiet
pip install python-docx==1.1.0 --quiet
pip install mysql-connector-python==8.2.0 --quiet
pip install python-dotenv==1.0.0 --quiet

echo ✅ All Python packages installed!
echo.

echo ========================================================
echo STEP 2: MySQL Database Setup
echo ========================================================
echo.
echo IMPORTANT: Make sure MySQL Server is running!
echo.
echo Your MySQL Configuration:
echo   Host: localhost
echo   Port: 3306
echo   User: root
echo   Password: Aryan@2007
echo   Database: resumeai
echo.

echo Please complete these steps:
echo   1. Open MySQL Workbench
echo   2. Connect to your MySQL server (localhost)
echo   3. Go to File → Open SQL Script
echo   4. Select: database_setup.sql
echo   5. Click Execute (lightning bolt icon)
echo.

set /p ready="Have you completed the MySQL setup? (Y/N): "
if /i not "%ready%"=="Y" (
    echo.
    echo Please complete the MySQL setup first, then run this script again.
    echo.
    echo Quick steps:
    echo   1. Open MySQL Workbench
    echo   2. Run database_setup.sql script
    echo   3. Run this script again
    echo.
    pause
    exit /b 0
)

echo.
echo ========================================================
echo STEP 3: Starting ResumeAI Server
echo ========================================================
echo.

echo Initializing server...
echo.

python app-mysql.py

echo.
echo ========================================================
echo Server stopped. Press any key to exit.
echo ========================================================
pause
