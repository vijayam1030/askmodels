@echo off
title Flask App Restart - Enhanced Summary Fix
echo.
echo ========================================
echo    FIXING ENHANCED SUMMARY ERROR
echo ========================================
echo.
echo This script will restart your Flask app to apply
echo the backend fixes for the enhanced summary feature.
echo.
echo Steps:
echo 1. Stop the current Flask app (if running)
echo 2. Restart with the fixed code
echo 3. Test the enhanced summary feature
echo.
echo ========================================
echo.

cd /d "c:\Users\wanth\hharry\models\python\askmodels"

echo 📁 Current directory: %CD%
echo.

echo 🔄 Starting Flask app with enhanced summary fixes...
echo.
echo ⚠️  If you see "Address already in use" error:
echo    - Stop the other Flask instance first (Ctrl+C)
echo    - Then run this script again
echo.

python unified_app.py

echo.
echo ========================================
echo If the app started successfully, the enhanced
echo summary error should now be fixed!
echo ========================================
pause
