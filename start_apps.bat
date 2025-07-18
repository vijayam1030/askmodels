@echo off
echo Starting Multi-Model Query Applications...
echo.

echo Starting Dashboard App on port 5001...
start "Dashboard App" cmd /k "python dashboard_app.py"

timeout /t 3 /nobreak

echo Starting Unified App on port 5000...
start "Unified App" cmd /k "python unified_app.py"

echo.
echo Both applications started!
echo Dashboard: http://localhost:5001
echo Main App: http://localhost:5000
echo.
pause
