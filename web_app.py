#!/usr/bin/env python3
"""
Web UI for Multi-Model Query Application
Flask-based web interface for querying multiple models through Ollama.
"""

import asyncio
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import threading
import queue
import time

from models import (
    OllamaModelManager, 
    ConfigManager, 
    QuestionType, 
    PromptEnhancer,
    ModelResponse
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
config_manager = ConfigManager()
model_manager = OllamaModelManager(config_manager)
available_models = []

class WebStreamingHandler:
    """Handles streaming responses for web interface."""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.responses = {}
        self.start_times = {}
    
    async def streaming_callback(self, model_name: str, chunk: str, is_done: bool):
        """Callback for streaming model responses."""
        if chunk and not is_done:
            # Initialize model tracking if first chunk
            if model_name not in self.responses:
                self.responses[model_name] = ""
                self.start_times[model_name] = time.time()
                socketio.emit('model_started', {
                    'model': model_name,
                    'session_id': self.session_id
                })
            
            # Add chunk to response
            self.responses[model_name] += chunk
            
            # Emit chunk to client
            socketio.emit('chunk_received', {
                'model': model_name,
                'chunk': chunk,
                'session_id': self.session_id
            })
            
        elif is_done:
            # Model completed
            elapsed_time = time.time() - self.start_times.get(model_name, 0)
            socketio.emit('model_completed', {
                'model': model_name,
                'elapsed_time': elapsed_time,
                'session_id': self.session_id
            })

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/models')
def get_models():
    """Get available models."""
    global available_models
    available_models = model_manager.get_available_models()
    
    coding_models = model_manager.get_models_for_question_type(QuestionType.CODING)
    
    return jsonify({
        'success': True,
        'models': available_models,
        'coding_models': coding_models,
        'total_count': len(available_models),
        'coding_count': len(coding_models)
    })

@app.route('/api/config')
def get_config():
    """Get current configuration."""
    return jsonify({
        'success': True,
        'config': config_manager.config
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    emit('connected', {'session_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")

@socketio.on('query_models')
def handle_query(data):
    """Handle model query request."""
    question = data.get('question', '').strip()
    question_type_str = data.get('type', 'general')
    use_streaming = data.get('streaming', True)
    session_id = request.sid
    
    if not question:
        emit('error', {'message': 'Please provide a question'})
        return
    
    # Determine question type
    question_type = QuestionType.CODING if question_type_str == 'coding' else QuestionType.GENERAL
    
    # Start processing in background
    thread = threading.Thread(
        target=process_query_async,
        args=(question, question_type, use_streaming, session_id)
    )
    thread.daemon = True
    thread.start()

def process_query_async(question: str, question_type: QuestionType, use_streaming: bool, session_id: str):
    """Process query asynchronously."""
    try:
        # Run in new event loop for thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            process_query(question, question_type, use_streaming, session_id)
        )
        
        loop.close()
        
    except Exception as e:
        socketio.emit('error', {
            'message': f'Error processing query: {str(e)}',
            'session_id': session_id
        })

async def process_query(question: str, question_type: QuestionType, use_streaming: bool, session_id: str):
    """Process the actual query."""
    try:
        # Get appropriate models
        models_to_query = model_manager.get_models_for_question_type(question_type)
        
        if not models_to_query:
            socketio.emit('error', {
                'message': 'No suitable models found for this question type',
                'session_id': session_id
            })
            return
        
        # Enhance prompt
        enhanced_prompt = PromptEnhancer.enhance_prompt(question, question_type)
        
        # Emit query start
        socketio.emit('query_started', {
            'question': question,
            'type': question_type.value,
            'models': models_to_query,
            'streaming': use_streaming,
            'session_id': session_id
        })
        
        if use_streaming:
            # Setup streaming handler
            streaming_handler = WebStreamingHandler(session_id)
            
            # Query with streaming
            responses = await model_manager.query_multiple_models(
                models_to_query,
                enhanced_prompt,
                max_concurrent=3,
                stream=True,
                callback=streaming_handler.streaming_callback
            )
        else:
            # Query without streaming
            responses = await model_manager.query_multiple_models(
                models_to_query,
                enhanced_prompt,
                max_concurrent=3,
                stream=False
            )
            
            # Emit all responses at once
            for response in responses:
                socketio.emit('response_received', {
                    'model': response.model_name,
                    'response': response.response,
                    'response_time': response.response_time,
                    'error': response.error,
                    'session_id': session_id
                })
        
        # Emit completion summary
        successful = [r for r in responses if r.is_successful()]
        failed = [r for r in responses if not r.is_successful()]
        
        socketio.emit('query_completed', {
            'successful_count': len(successful),
            'failed_count': len(failed),
            'failed_models': [{'model': r.model_name, 'error': r.error} for r in failed],
            'session_id': session_id
        })
        
    except Exception as e:
        socketio.emit('error', {
            'message': f'Error during query processing: {str(e)}',
            'session_id': session_id
        })

if __name__ == '__main__':
    print("🚀 Starting Multi-Model Query Web UI...")
    print("📡 Server will be available at: http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
