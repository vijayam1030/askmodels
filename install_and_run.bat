@echo off
echo Installing missing dependencies...
pip install psutil
echo.
echo Starting Flask app with enhanced debugging...
python unified_app.py
pause
