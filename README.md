# Multi-Model Query Application

A Python application that queries multiple AI models through Ollama for both general and coding questions, providing responses from each model with performance metrics.

## Features

- 🤖 **Multi-Model Support**: Query multiple models simultaneously through Ollama
- 💻 **Coding-Specific Models**: Automatically identifies and prioritizes coding-capable models for programming questions
- 📝 **General Questions**: Use all available models for general queries
- ⚡ **Streaming Responses**: Real-time streaming of responses as they arrive (3 models at a time)
- 🔄 **Batch Processing**: Process models in configurable batches to prevent overwhelming the system
- ⏱️ **Response Options**: Choose between streaming responses or waiting for all models to complete
- 📊 **Response Metrics**: Shows response time and success/failure status for each model
- ⚙️ **Configurable**: Easy configuration through JSON config file
- 🎨 **Clean UI**: Emoji-rich console interface for better user experience

## Prerequisites

1. **Ollama**: Make sure Ollama is installed and running
   ```bash
   # Install Ollama (visit https://ollama.ai for installation instructions)
   # Then pull some models, for example:
   ollama pull llama3.1
   ollama pull codellama
   ollama pull deepseek-coder
   ```

2. **Python 3.7+**: The application requires Python 3.7 or higher

## Installation

1. Clone or download this project to your local machine

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Web Interface (Recommended)

1. **Start the web interface**:
   ```bash
   python run_web.py
   # OR on Windows:
   run_web.bat
   ```

2. **Open your browser** to: http://localhost:5000

3. **Use the web interface**:
   - Enter your question in the text area
   - Choose question type (General or Coding)
   - Toggle streaming on/off
   - Click "Query Models" to start

### Console Interface

Run the console application:
```bash
python main.py
```

### Menu Options

1. **📝 Ask General Question (Streaming)**: Query all available models with real-time streaming responses
2. **💻 Ask Coding Question (Streaming)**: Query coding-capable models with streaming responses and enhanced prompts
3. **📄 Ask General Question (Wait for All)**: Query all models and wait for complete responses before displaying
4. **🖥️ Ask Coding Question (Wait for All)**: Query coding models and wait for all responses
5. **📊 Show Available Models**: Display all models and their categories
6. **🔄 Refresh Models**: Reload the list of available models from Ollama
7. **⚙️ Show Configuration**: Display current application settings
8. **🚪 Exit**: Close the application

## Configuration

The application uses a `config.json` file for configuration:

```json
{
  "ollama_url": "http://localhost:11434",
  "coding_models": [
    "codellama",
    "deepseek-coder",
    "codegemma", 
    "starcoder",
    "magicoder",
    "phind-codellama",
    "wizardcoder",
    "llama3",
    "llama3.1",
    "qwen2.5-coder",
    "granite-code"
  ],
  "request_timeout": 60,
  "max_concurrent_requests": 5
}
```

### Configuration Options

- `ollama_url`: The URL where Ollama is running (default: http://localhost:11434)
- `coding_models`: List of model name patterns that are considered coding-capable
- `request_timeout`: Timeout in seconds for each model request
- `max_concurrent_requests`: Maximum number of concurrent requests (default: 3 for optimal streaming)
- `default_batch_size`: Number of models to process simultaneously in streaming mode

## Project Structure

```
askmodels/
├── main.py           # Console application entry point
├── web_app.py        # Web application (Flask + SocketIO)
├── run_web.py        # Web UI launcher script
├── run_web.bat       # Windows web UI launcher
├── models.py         # Model management and Ollama interaction
├── ui.py            # Console UI and display formatting
├── templates/        # Web UI templates
│   └── index.html   # Main web interface
├── config.json      # Configuration file
├── requirements.txt # Python dependencies
└── README.md       # This file
```

## Example Usage

### General Question
```
📝 Enter your general question: What is the capital of France?

🌐 Querying 3 models: llama3.1, codellama, deepseek-coder

📊 RESULTS
✅ 3 successful • ❌ 0 failed

🤖 MODEL: llama3.1
⏱️  RESPONSE TIME: 1.23s
💬 RESPONSE:
The capital of France is Paris...
```

### Coding Question
```
💻 Enter your coding question: How do I implement a binary search in Python?

💻 Querying 2 models: codellama, deepseek-coder

📊 RESULTS
✅ 2 successful • ❌ 0 failed

🤖 MODEL: codellama
⏱️  RESPONSE TIME: 2.45s
💬 RESPONSE:
Here's an implementation of binary search in Python:

def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    ...
```

## Troubleshooting

### Common Issues

1. **No models found**
   - Ensure Ollama is running: `ollama serve`
   - Check if models are installed: `ollama list`
   - Verify the Ollama URL in config.json

2. **Connection errors**
   - Check if Ollama is accessible at the configured URL
   - Verify firewall settings if using a remote Ollama instance

3. **Slow responses**
   - Reduce `max_concurrent_requests` in config.json
   - Increase `request_timeout` for larger models

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

## License

This project is open source and available under the MIT License.
