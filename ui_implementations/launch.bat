@echo off
echo 🤖 Multi-Model AI Assistant - Launch Script
echo.

echo Checking if Flask backend is running...
curl -s http://localhost:5000/api/models >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Flask backend not running! Please start unified_app.py first.
    echo.
    echo To start the Flask backend:
    echo   cd ..
    echo   python unified_app.py
    echo.
    pause
    exit /b 1
)

echo ✅ Flask backend is running!
echo.

echo Available UI Technologies:
echo.
echo 1. Flask + SocketIO (Current - Port 5000)
echo 2. Streamlit (Port 8501)
echo 3. React (Port 3000)
echo 4. Gradio (Port 7860)
echo 5. Technology Selector (HTML)
echo.

set /p choice="Choose a technology (1-5): "

if "%choice%"=="1" (
    echo Launching Flask app...
    start http://localhost:5000
) else if "%choice%"=="2" (
    echo Installing Streamlit requirements...
    pip install -r requirements_streamlit.txt
    echo Launching Streamlit app...
    streamlit run streamlit_app.py
) else if "%choice%"=="3" (
    echo Setting up React app...
    cd react_app
    if not exist node_modules (
        echo Installing React dependencies...
        npm install
    )
    echo Launching React app...
    npm start
) else if "%choice%"=="4" (
    echo Installing Gradio requirements...
    pip install -r requirements_gradio.txt
    echo Launching Gradio app...
    python gradio_app.py
) else if "%choice%"=="5" (
    echo Opening Technology Selector...
    start index.html
) else (
    echo Invalid choice. Please run the script again.
    pause
    exit /b 1
)

echo.
echo ✅ Application launched successfully!
pause
