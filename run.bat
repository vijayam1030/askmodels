@echo off
REM Multi-Model Query Application Launcher
REM This script helps run the application with proper error handling

echo.
echo ========================================
echo  Multi-Model Query Application
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
if not exist "main.py" (
    echo ERROR: main.py not found
    echo Please run this script from the project directory
    pause
    exit /b 1
)

REM Run setup check
echo Checking setup...
python setup.py
if errorlevel 1 (
    echo.
    echo Setup check failed. Please resolve the issues above.
    pause
    exit /b 1
)

echo.
echo Starting application...
echo.

REM Run the main application
python main.py

echo.
echo Application closed.
pause
