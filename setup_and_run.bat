@echo off
echo Installing required dependencies...
echo.

REM Install psutil
echo Installing psutil...
pip install psutil

REM Install other common dependencies that might be missing
echo Installing additional dependencies...
pip install flask flask-socketio requests aiohttp openai anthropic

echo.
echo All dependencies installed!
echo.
echo Starting Flask app with improved debugging...
python unified_app.py
pause
