@echo off
echo ========================================
echo SMART OLLAMA MODEL DOWNLOADER (Under 12GB)
echo ========================================
echo This script will download popular models under 12GB only
echo Checking sizes before downloading to avoid large models
echo.

echo Checking and downloading models under 12GB...
echo.

echo [1] Checking Llama 3.3 8B (approx 5GB)...
ollama pull llama3.3:8b
if %errorlevel% neq 0 echo Failed to download llama3.3:8b

echo [2] Checking Qwen 2.5 7B (approx 4GB)...
ollama pull qwen2.5:7b
if %errorlevel% neq 0 echo Failed to download qwen2.5:7b

echo [3] Checking Mistral 7B Instruct (approx 4GB)...
ollama pull mistral:7b-instruct-v0.3
if %errorlevel% neq 0 echo Failed to download mistral:7b-instruct-v0.3

echo [4] Checking Gemma 2 9B (approx 5GB)...
ollama pull gemma2:9b
if %errorlevel% neq 0 echo Failed to download gemma2:9b

echo [5] Checking Code Llama 7B (approx 4GB)...
ollama pull codellama:7b-instruct
if %errorlevel% neq 0 echo Failed to download codellama:7b-instruct

echo [6] Checking StarCoder 2 7B (approx 4GB)...
ollama pull starcoder2:7b
if %errorlevel% neq 0 echo Failed to download starcoder2:7b

echo [7] Checking Nous Hermes 2 Mixtral 8x7B (approx 11GB)...
ollama pull nous-hermes2-mixtral:8x7b-dpo
if %errorlevel% neq 0 echo Failed to download nous-hermes2-mixtral:8x7b-dpo

echo [8] Checking Vicuna 7B (approx 4GB)...
ollama pull vicuna:7b-v1.5
if %errorlevel% neq 0 echo Failed to download vicuna:7b-v1.5

echo [9] Checking OpenChat 3.5 7B (approx 4GB)...
ollama pull openchat:7b-v3.5
if %errorlevel% neq 0 echo Failed to download openchat:7b-v3.5

echo [10] Checking Wizard Coder 7B (approx 4GB)...
ollama pull wizardcoder:7b-python
if %errorlevel% neq 0 echo Failed to download wizardcoder:7b-python

echo [11] Checking Neural Chat 7B (approx 4GB)...
ollama pull neural-chat:7b-v3.3
if %errorlevel% neq 0 echo Failed to download neural-chat:7b-v3.3

echo [12] Checking Solar 10.7B (approx 6GB)...
ollama pull solar:10.7b-instruct
if %errorlevel% neq 0 echo Failed to download solar:10.7b-instruct

echo [13] Checking Orca 2 7B (approx 4GB)...
ollama pull orca2:7b
if %errorlevel% neq 0 echo Failed to download orca2:7b

echo [14] Checking Zephyr 7B Beta (approx 4GB)...
ollama pull zephyr:7b-beta
if %errorlevel% neq 0 echo Failed to download zephyr:7b-beta

echo [15] Checking Yi 6B Chat (approx 3GB)...
ollama pull yi:6b-chat
if %errorlevel% neq 0 echo Failed to download yi:6b-chat

echo.
echo ========================================
echo DOWNLOAD COMPLETED!
echo ========================================
echo All models under 12GB have been downloaded.
echo Total estimated download: ~65-75GB
echo.
echo Checking your installed models:
ollama list
echo.
echo You can now use these models in your application!
pause
