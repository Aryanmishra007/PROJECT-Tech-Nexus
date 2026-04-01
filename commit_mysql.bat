@echo off
echo ================================
echo   Committing to GitHub
echo ================================
echo.

cd /d "%~dp0"

echo Checking git status...
echo.
git status
echo.

echo ⚠️  IMPORTANT: .env file will NOT be committed (password protected)
echo.

echo Adding files...
git add test_mysql_connection.py
git add test_mysql.bat
git add STRIPE_SETUP.md
echo.

echo Creating commit...
git commit -m "Configure MySQL database connection and testing tools

- Add MySQL connection test script
- Fix database name in configuration (projectnexai_ai)
- Add comprehensive setup documentation
- MySQL now working locally with all features

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ================================
echo ✅ Done!
echo ================================
pause
