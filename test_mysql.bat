@echo off
echo ================================
echo    MySQL Connection Test
echo ================================
echo.

cd /d "%~dp0"
python test_mysql_connection.py

echo.
echo ================================
echo.
echo Now starting Flask app...
echo.
python app.py
