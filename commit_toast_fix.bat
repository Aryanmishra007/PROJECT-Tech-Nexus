@echo off
echo ================================
echo   Fixing Toast Error Messages
echo ================================
echo.

cd /d "%~dp0"

echo Adding files...
git add script.js

echo.
echo Creating commit...
git commit -m "Fix toast error message visibility with debugging

- Add console logging to track toast creation
- Fallback to alert if toast container missing
- Ensure error messages display on login failure
- Better error message visibility

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ================================
echo ✅ Done! Changes pushed to GitHub
echo ================================
echo.
echo Your live site will auto-deploy in 2-3 minutes
pause
