@echo off
echo ========================================
echo SELECTIVE MODEL DOWNLOADER (Under 12GB)
echo ========================================
echo Choose which models to download (all verified under 12GB):
echo.

:menu
cls
echo ========================================
echo AVAILABLE MODELS UNDER 12GB
echo ========================================
echo.
echo GENERAL PURPOSE MODELS:
echo [1]  Llama 3.3 8B (~5GB) - Latest Meta model
echo [2]  Qwen 2.5 7B (~4GB) - Excellent multilingual
echo [3]  Mistral 7B Instruct (~4GB) - Fast and efficient
echo [4]  Gemma 2 9B (~5GB) - Google's latest
echo [5]  Vicuna 7B (~4GB) - Conversation specialist
echo [6]  OpenChat 7B (~4GB) - Open source chat
echo [7]  Solar 10.7B (~6GB) - High performance
echo [8]  Orca 2 7B (~4GB) - Microsoft research
echo [9]  Zephyr 7B Beta (~4GB) - Instruction tuned
echo [10] Yi 6B Chat (~3GB) - Compact and efficient
echo.
echo CODING MODELS:
echo [11] Code Llama 7B Instruct (~4GB) - Code generation
echo [12] StarCoder 2 7B (~4GB) - Advanced coding
echo [13] Wizard Coder 7B Python (~4GB) - Python specialist
echo [14] Neural Chat 7B (~4GB) - Intel's coding model
echo.
echo SPECIALIZED MODELS:
echo [15] Nous Hermes 2 Mixtral 8x7B (~11GB) - Advanced reasoning
echo.
echo BULK OPTIONS:
echo [A] Download ALL models above (~75GB total)
echo [G] Download General Purpose only (~35GB)
echo [C] Download Coding models only (~16GB)
echo [R] Recommended mix (5 best models ~20GB)
echo [Q] Quit
echo.

set /p choice="Enter your choice (1-15, A, G, C, R, or Q): "

if /i "%choice%"=="1" (
    echo Downloading Llama 3.3 8B...
    ollama pull llama3.3:8b
    goto continue
)
if /i "%choice%"=="2" (
    echo Downloading Qwen 2.5 7B...
    ollama pull qwen2.5:7b
    goto continue
)
if /i "%choice%"=="3" (
    echo Downloading Mistral 7B Instruct...
    ollama pull mistral:7b-instruct-v0.3
    goto continue
)
if /i "%choice%"=="4" (
    echo Downloading Gemma 2 9B...
    ollama pull gemma2:9b
    goto continue
)
if /i "%choice%"=="5" (
    echo Downloading Vicuna 7B...
    ollama pull vicuna:7b-v1.5
    goto continue
)
if /i "%choice%"=="6" (
    echo Downloading OpenChat 7B...
    ollama pull openchat:7b-v3.5
    goto continue
)
if /i "%choice%"=="7" (
    echo Downloading Solar 10.7B...
    ollama pull solar:10.7b-instruct
    goto continue
)
if /i "%choice%"=="8" (
    echo Downloading Orca 2 7B...
    ollama pull orca2:7b
    goto continue
)
if /i "%choice%"=="9" (
    echo Downloading Zephyr 7B Beta...
    ollama pull zephyr:7b-beta
    goto continue
)
if /i "%choice%"=="10" (
    echo Downloading Yi 6B Chat...
    ollama pull yi:6b-chat
    goto continue
)
if /i "%choice%"=="11" (
    echo Downloading Code Llama 7B Instruct...
    ollama pull codellama:7b-instruct
    goto continue
)
if /i "%choice%"=="12" (
    echo Downloading StarCoder 2 7B...
    ollama pull starcoder2:7b
    goto continue
)
if /i "%choice%"=="13" (
    echo Downloading Wizard Coder 7B Python...
    ollama pull wizardcoder:7b-python
    goto continue
)
if /i "%choice%"=="14" (
    echo Downloading Neural Chat 7B...
    ollama pull neural-chat:7b-v3.3
    goto continue
)
if /i "%choice%"=="15" (
    echo Downloading Nous Hermes 2 Mixtral 8x7B...
    ollama pull nous-hermes2-mixtral:8x7b-dpo
    goto continue
)
if /i "%choice%"=="A" (
    echo Downloading ALL models...
    call download_under_12gb.bat
    goto continue
)
if /i "%choice%"=="G" (
    echo Downloading General Purpose models...
    ollama pull llama3.3:8b
    ollama pull qwen2.5:7b
    ollama pull mistral:7b-instruct-v0.3
    ollama pull gemma2:9b
    ollama pull vicuna:7b-v1.5
    ollama pull openchat:7b-v3.5
    ollama pull solar:10.7b-instruct
    ollama pull orca2:7b
    ollama pull zephyr:7b-beta
    ollama pull yi:6b-chat
    goto continue
)
if /i "%choice%"=="C" (
    echo Downloading Coding models...
    ollama pull codellama:7b-instruct
    ollama pull starcoder2:7b
    ollama pull wizardcoder:7b-python
    ollama pull neural-chat:7b-v3.3
    goto continue
)
if /i "%choice%"=="R" (
    echo Downloading Recommended mix...
    echo - Llama 3.3 8B (general)
    ollama pull llama3.3:8b
    echo - Qwen 2.5 7B (multilingual)
    ollama pull qwen2.5:7b
    echo - Code Llama 7B (coding)
    ollama pull codellama:7b-instruct
    echo - Mistral 7B (efficient)
    ollama pull mistral:7b-instruct-v0.3
    echo - Solar 10.7B (advanced)
    ollama pull solar:10.7b-instruct
    goto continue
)
if /i "%choice%"=="Q" (
    echo Goodbye!
    exit /b
)

echo Invalid choice. Please try again.
pause
goto menu

:continue
echo.
echo Download completed! Current models:
ollama list
echo.
echo Press any key to return to menu...
pause >nul
goto menu
