@echo off
REM Multi-Model Query Web UI Launcher
REM This script starts the web-based user interface

echo.
echo ========================================
echo  Multi-Model Query Web UI
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "web_app.py" (
    echo ERROR: web_app.py not found
    echo Please run this script from the project directory
    pause
    exit /b 1
)

echo Starting Web UI...
echo The application will open in your browser automatically
echo Manual URL: http://localhost:5000
echo.
echo Make sure Ollama is running: ollama serve
echo Press Ctrl+C to stop the server
echo.

REM Run the web application
python run_web.py

echo.
echo Web server stopped.
pause
