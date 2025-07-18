@echo off
echo ================================
echo SELECTIVE OLLAMA MODEL DOWNLOADER
echo ================================
echo Choose which models to download (all under 12GB):
echo.

:menu
echo [1] Llama 3.3 (8GB) - Latest Meta model
echo [2] Qwen 2.5 7B (4GB) - Excellent multilingual
echo [3] Qwen 2.5 14B (8GB) - Larger multilingual  
echo [4] Mistral 7B Instruct (4GB) - Fast and efficient
echo [5] Gemma 2 9B (5GB) - Google's latest
echo [6] Phi 3 14B (8GB) - Microsoft's model
echo [7] StarCoder 2 7B (4GB) - Advanced coding
echo [8] Code Qwen 7B (4GB) - Multilingual coding
echo [9] Nous Hermes 2 10.7B (6GB) - Chat optimized
echo [10] Vicuna 7B (4GB) - Conversation model
echo [11] OpenChat 7B (4GB) - Open source chat
echo [12] Neural Chat 7B (4GB) - Intel's model
echo [13] Granite Code 8B (5GB) - IBM's code model
echo [14] DeepSeek R1 7B (4GB) - Reasoning model
echo [15] Wizard Coder 7B (4GB) - Code generation
echo [A] Download ALL models above
echo [Q] Quit
echo.

set /p choice="Enter your choice (1-15, A, or Q): "

if /i "%choice%"=="1" (
    echo Downloading Llama 3.3...
    ollama pull llama3.3:latest
    goto menu
)
if /i "%choice%"=="2" (
    echo Downloading Qwen 2.5 7B...
    ollama pull qwen2.5:7b
    goto menu
)
if /i "%choice%"=="3" (
    echo Downloading Qwen 2.5 14B...
    ollama pull qwen2.5:14b
    goto menu
)
if /i "%choice%"=="4" (
    echo Downloading Mistral 7B Instruct...
    ollama pull mistral:7b-instruct
    goto menu
)
if /i "%choice%"=="5" (
    echo Downloading Gemma 2 9B...
    ollama pull gemma2:9b
    goto menu
)
if /i "%choice%"=="6" (
    echo Downloading Phi 3 14B...
    ollama pull phi3:14b
    goto menu
)
if /i "%choice%"=="7" (
    echo Downloading StarCoder 2 7B...
    ollama pull starcoder2:7b
    goto menu
)
if /i "%choice%"=="8" (
    echo Downloading Code Qwen 7B...
    ollama pull codeqwen:7b
    goto menu
)
if /i "%choice%"=="9" (
    echo Downloading Nous Hermes 2...
    ollama pull nous-hermes2:10.7b
    goto menu
)
if /i "%choice%"=="10" (
    echo Downloading Vicuna 7B...
    ollama pull vicuna:7b
    goto menu
)
if /i "%choice%"=="11" (
    echo Downloading OpenChat 7B...
    ollama pull openchat:7b
    goto menu
)
if /i "%choice%"=="12" (
    echo Downloading Neural Chat 7B...
    ollama pull neural-chat:7b
    goto menu
)
if /i "%choice%"=="13" (
    echo Downloading Granite Code 8B...
    ollama pull granite-code:8b
    goto menu
)
if /i "%choice%"=="14" (
    echo Downloading DeepSeek R1 7B...
    ollama pull deepseek-r1:7b
    goto menu
)
if /i "%choice%"=="15" (
    echo Downloading Wizard Coder 7B...
    ollama pull wizard-coder:7b
    goto menu
)
if /i "%choice%"=="A" (
    echo Downloading ALL models...
    call download_top_models.bat
    goto menu
)
if /i "%choice%"=="Q" (
    echo Goodbye!
    exit /b
)

echo Invalid choice. Please try again.
goto menu
