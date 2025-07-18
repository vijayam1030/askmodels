@echo off
echo Downloading TOP recommended Ollama models under 12GB...
echo This will download about 15-20 models totaling around 80-100GB
echo Press Ctrl+C to cancel if you want to select specific models instead
echo.
timeout /t 10

echo [1/15] Downloading Llama 3.3 (8GB) - Latest Meta model...
ollama pull llama3.3:latest

echo [2/15] Downloading Qwen 2.5 7B (4GB) - Excellent multilingual...
ollama pull qwen2.5:7b

echo [3/15] Downloading Qwen 2.5 14B (8GB) - Larger multilingual...
ollama pull qwen2.5:14b

echo [4/15] Downloading Mistral 7B Instruct (4GB) - Fast and efficient...
ollama pull mistral:7b-instruct

echo [5/15] Downloading Gemma 2 9B (5GB) - Google's model...
ollama pull gemma2:9b

echo [6/15] Downloading Phi 3 14B (8GB) - Microsoft's model...
ollama pull phi3:14b

echo [7/15] Downloading StarCoder 2 7B (4GB) - Advanced code model...
ollama pull starcoder2:7b

echo [8/15] Downloading Code Qwen 7B (4GB) - Multilingual coding...
ollama pull codeqwen:7b

echo [9/15] Downloading Nous Hermes 2 10.7B (6GB) - Chat optimized...
ollama pull nous-hermes2:10.7b

echo [10/15] Downloading Vicuna 7B (4GB) - Conversation model...
ollama pull vicuna:7b

echo [11/15] Downloading OpenChat 7B (4GB) - Open source chat...
ollama pull openchat:7b

echo [12/15] Downloading Neural Chat 7B (4GB) - Intel's model...
ollama pull neural-chat:7b

echo [13/15] Downloading Granite Code 8B (5GB) - IBM's code model...
ollama pull granite-code:8b

echo [14/15] Downloading DeepSeek R1 7B (4GB) - Reasoning model...
ollama pull deepseek-r1:7b

echo [15/15] Downloading Wizard Coder 7B (4GB) - Code generation...
ollama pull wizard-coder:7b

echo.
echo ================================
echo ALL DOWNLOADS COMPLETED!
echo ================================
echo Run "ollama list" to see all installed models.
echo Total models downloaded: 15
echo Estimated total size: ~80GB
echo.
echo You can now use these models in your application!
pause
