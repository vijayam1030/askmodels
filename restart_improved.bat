@echo off
echo Restarting Flask app with improved model selection...
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo Starting Flask app...
python unified_app.py
pause
