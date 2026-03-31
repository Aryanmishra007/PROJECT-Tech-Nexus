@echo off
echo ========================================================
echo NexaAI - AI Skill Gap Platform
echo ========================================================
echo.

echo [1/4] Installing Python Dependencies...
pip install flask flask-cors werkzeug PyPDF2 python-docx mysql-connector-python python-dotenv
if %errorlevel% neq 0 (
    echo Error installing dependencies!
    pause
    exit /b 1
)
echo.
echo Dependencies installed successfully!
echo.

echo [2/4] Checking MySQL Connection...
echo Make sure MySQL Server is running!
echo Database: projectnexai_ai
echo.

echo [3/4] MySQL Configuration:
echo    Host: 127.0.0.1
echo    User: root
echo    Database: projectnexai_ai
echo.

echo [4/4] Starting the application...
echo.
echo ========================================================
echo Opening browser at http://localhost:5000
echo.
echo ADMIN LOGIN:
echo    Email: admin@nexaai.com
echo    Password: admin123
echo.
echo NEW USER: 
echo    Click "Create an account" to sign up
echo ========================================================
echo.

python app.py

pause
