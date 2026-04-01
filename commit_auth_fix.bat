@echo off
echo ================================
echo   Committing Auth Improvements
echo ================================
echo.

cd /d "%~dp0"

echo Adding files...
git add app.py script.js

echo.
echo Creating commit...
git commit -m "Improve login/signup UX with better error messages

- Show specific error when password is incorrect
- Clear forms after successful login/signup
- Auth page properly hides after login
- Error messages stay visible longer (5 seconds)
- Better user feedback on authentication errors

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
