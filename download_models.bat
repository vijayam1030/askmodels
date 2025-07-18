@echo off
echo Downloading popular Ollama models under 12GB...
echo This may take a while depending on your internet connection.
echo.

echo Downloading Llama 3.3 (8GB)...
ollama pull llama3.3:latest

echo Downloading Qwen 2.5 models...
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b

echo Downloading Code-focused models...
ollama pull starcoder2:7b
ollama pull codeqwen:7b

echo Downloading Gemma models...
ollama pull gemma2:9b
ollama pull gemma2:7b

echo Downloading Mistral models...
ollama pull mistral:7b-instruct
ollama pull mixtral:8x7b

echo Downloading Phi models...
ollama pull phi3:14b
ollama pull phi3.5:latest

echo Downloading LLaVA vision models...
ollama pull llava:34b

echo Downloading specialized models...
ollama pull nous-hermes2:10.7b
ollama pull vicuna:7b
ollama pull wizard-coder:7b
ollama pull openchat:7b
ollama pull neural-chat:7b

echo Downloading newer models...
ollama pull granite-code:8b
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:14b

echo All downloads completed!
echo Run "ollama list" to see all installed models.
pause
