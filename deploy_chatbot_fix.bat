@echo off
echo ================================
echo   Deploying Chatbot Fixes
echo ================================
echo.

cd /d "%~dp0"

echo Adding files...
git add app.py script.js

echo.
echo Creating commit...
git commit -m "Fix chatbot error handling and add offline fallbacks

- Add local fallback responses when Gemini AI is unavailable
- Handle greetings (hi, hello) with helpful career prompts
- Provide AI/ML skill guidance even when API is down
- Show clear session expiry messages instead of generic errors
- Parse non-JSON backend responses safely in frontend
- Surface specific backend errors to users for better UX

Fixes:
- 'hii' and 'ai &ml skil' now get helpful responses
- Session timeout shows clear message instead of vague error
- No more generic 'Sorry, I encountered an error' for all failures

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
echo.
pause
