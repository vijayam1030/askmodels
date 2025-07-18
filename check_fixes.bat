@echo off
echo ========================================
echo Flask App Enhanced Summary Fix Status
echo ========================================
echo.
echo This script will:
echo 1. Check if fixes are applied to the code
echo 2. Validate the Flask app configuration
echo 3. Provide restart instructions
echo.
echo IMPORTANT: This runs in a separate terminal from your Flask app
echo ========================================
echo.

cd /d "c:\Users\wanth\hharry\models\python\askmodels"

echo [1/3] Checking current directory...
echo Current directory: %CD%
echo.

echo [2/3] Checking if unified_app.py exists...
if exist unified_app.py (
    echo ✅ unified_app.py found
) else (
    echo ❌ unified_app.py not found
    pause
    exit /b 1
)
echo.

echo [3/3] Running code validation...
python validate_code_fix.py
echo.

echo ========================================
echo NEXT STEPS TO APPLY THE FIXES:
echo ========================================
echo 1. Go to the terminal where Flask is running
echo 2. Press Ctrl+C to stop the Flask app
echo 3. Run: python unified_app.py
echo 4. Test the enhanced summary feature
echo ========================================
echo.
pause
