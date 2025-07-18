# PowerShell script to check and apply enhanced summary fixes
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Enhanced Summary Fix - Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to project directory
$projectPath = "c:\Users\wanth\hharry\models\python\askmodels"
Set-Location $projectPath

Write-Host "📁 Current directory: $PWD" -ForegroundColor Green
Write-Host ""

# Check if files exist
if (Test-Path "unified_app.py") {
    Write-Host "✅ unified_app.py found" -ForegroundColor Green
} else {
    Write-Host "❌ unified_app.py not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

if (Test-Path "validate_code_fix.py") {
    Write-Host "✅ validate_code_fix.py found" -ForegroundColor Green
} else {
    Write-Host "❌ validate_code_fix.py not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

Write-Host ""
Write-Host "🔍 Running code validation..." -ForegroundColor Yellow
Write-Host ""

# Run the validation script
try {
    python validate_code_fix.py
    Write-Host ""
    Write-Host "✅ Code validation completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Error running validation: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚨 CRITICAL: Flask App Restart Required" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The enhanced summary error occurs because your Flask app" -ForegroundColor Yellow
Write-Host "is still running the OLD code without the fixes." -ForegroundColor Yellow
Write-Host ""
Write-Host "TO FIX THE ERROR:" -ForegroundColor Green
Write-Host "1. Go to the terminal where Flask is running" -ForegroundColor White
Write-Host "2. Press Ctrl+C to stop the Flask app" -ForegroundColor White
Write-Host "3. Run: python unified_app.py" -ForegroundColor White
Write-Host "4. Test the enhanced summary feature" -ForegroundColor White
Write-Host ""
Write-Host "The fixes are in the code but need app restart to take effect!" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

Read-Host "Press Enter to close this window"
