@echo off
echo ========================================================
echo Installing ResumeAI Dependencies
echo ========================================================
echo.

echo Installing Flask and extensions...
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install werkzeug==3.0.1

echo.
echo Installing PDF and Document parsers...
pip install PyPDF2==3.0.1
pip install python-docx==1.1.0

echo.
echo Installing MySQL connector...
pip install mysql-connector-python==8.2.0

echo.
echo Installing environment management...
pip install python-dotenv==1.0.0

echo.
echo ========================================================
echo ✅ All dependencies installed successfully!
echo ========================================================
echo.
echo Next steps:
echo 1. Make sure MySQL Server is running
echo 2. Open MySQL Workbench and run database_setup.sql
echo 3. Run start.bat to launch the application
echo.

pause
