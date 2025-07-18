@echo off
echo Opening PowerShell to check Enhanced Summary fix status...
powershell -ExecutionPolicy Bypass -File "check_fix_status.ps1"
pause
