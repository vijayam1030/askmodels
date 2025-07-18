# Multi-Model AI Assistant - UI Implementations

This folder contains multiple UI implementations of the Multi-Model AI Assistant, allowing you to choose your preferred technology for interacting with AI models.

## Available Technologies

### 1. Flask + SocketIO (Current Implementation)
- **Location**: `../unified_app.py` and `../templates/unified.html`
- **Port**: 5000
- **Features**: Full-featured with real-time updates, comprehensive debate system, cancel functionality
- **Launch**: `python unified_app.py`

### 2. Streamlit
- **Location**: `streamlit_app.py`
- **Port**: 8501
- **Features**: Data science friendly interface with interactive widgets
- **Launch**: `streamlit run streamlit_app.py`
- **Requirements**: `pip install -r requirements_streamlit.txt`

### 3. React
- **Location**: `react_app/`
- **Port**: 3000
- **Features**: Modern web application with rich interactivity
- **Setup**: 
  ```bash
  cd react_app
  npm install
  npm start
  ```

### 4. Gradio
- **Location**: `gradio_app.py`
- **Port**: 7860
- **Features**: ML-focused interface with easy sharing capabilities
- **Launch**: `python gradio_app.py`
- **Requirements**: `pip install -r requirements_gradio.txt`

## Quick Start

1. **Start the main page**: Open `index.html` in your browser
2. **Ensure Flask backend is running**: The Flask app (`unified_app.py`) must be running on port 5000 for all UIs to work
3. **Choose your preferred technology**: Click on any technology card to launch that implementation

## Technology Comparison

| Feature | Flask | Streamlit | React | Gradio |
|---------|-------|-----------|-------|--------|
| Real-time updates | ✅ | ⚠️ | ✅ | ⚠️ |
| Model specialization | ✅ | ✅ | ✅ | ✅ |
| Debate system | ✅ | ✅ | ✅ | ✅ |
| Cancel functionality | ✅ | ⚠️ | ✅ | ⚠️ |
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Responsive design | ✅ | ✅ | ✅ | ✅ |
| Easy deployment | ⚠️ | ✅ | ⚠️ | ✅ |
| Custom styling | ✅ | ⚠️ | ✅ | ⚠️ |

## Installation

### Prerequisites
- Python 3.8+
- Flask backend running on port 5000
- Ollama with AI models installed

### For Streamlit:
```bash
pip install -r requirements_streamlit.txt
streamlit run streamlit_app.py
```

### For React:
```bash
cd react_app
npm install
npm start
```

### For Gradio:
```bash
pip install -r requirements_gradio.txt
python gradio_app.py
```

## Usage

1. **Start the Flask backend**: Make sure `unified_app.py` is running
2. **Choose your UI**: Open `index.html` and select your preferred technology
3. **Select models**: Choose which AI models to interact with
4. **Ask questions or start debates**: Use the Q&A mode for questions or Debate mode for discussions

## Features

All implementations include:
- **Q&A Mode**: Ask questions to multiple models simultaneously
- **Debate Mode**: Watch AI models debate topics in real-time
- **Dashboard**: Monitor system resources and model performance
- **Model Management**: Group models by specialization and manage selections
- **Responsive Design**: Works on desktop and mobile devices

## Troubleshooting

### Common Issues:
1. **Connection Error**: Ensure Flask backend is running on port 5000
2. **No Models**: Make sure Ollama is running and has models installed
3. **Port Conflicts**: Check if ports 3000, 5000, 7860, or 8501 are in use

### Technology-Specific:
- **Streamlit**: If components don't update, try refreshing the page
- **React**: Run `npm install` if dependencies are missing
- **Gradio**: Check console for error messages if interface doesn't load

## Development

Each implementation follows the same API structure:
- `/api/models` - Get available models
- `/api/query` - Submit questions
- `/api/debate/start` - Start debates
- WebSocket events for real-time updates (Flask/React only)

## Contributing

To add a new UI technology:
1. Create a new implementation file
2. Follow the existing API structure
3. Add requirements file if needed
4. Update this README and `index.html`

## License

This project is part of the Multi-Model AI Assistant suite.
