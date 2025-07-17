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

def filter_large_models(models):
    """Filter out ultra-large models (70B+ parameters) that may be too resource intensive."""
    filtered_models = []
    excluded_models = []
    
    for model in models:
        model_lower = model.lower()
        
        # Check for ultra-large model indicators
        is_ultra_large = any([
            '70b' in model_lower,
            '72b' in model_lower,
            '405b' in model_lower,
            'llama3.1:70b' in model_lower,
            'llama3.2:70b' in model_lower,
            'qwen2.5:72b' in model_lower,
            'codellama:70b' in model_lower
        ])
        
        if is_ultra_large:
            excluded_models.append(model)
            print(f"⚠️  Excluding ultra-large model: {model} (likely 70B+ parameters)")
        else:
            filtered_models.append(model)
    
    if excluded_models:
        print(f"📊 Filtered {len(excluded_models)} ultra-large models, {len(filtered_models)} models available")
    
    return filtered_models

def initialize_models_on_startup():
    """Initialize and filter models when the application starts."""
    print("🔄 Initializing models on startup...")
    
    try:
        # Get all available models from Ollama
        all_models = model_manager.get_available_models(force_refresh=True)
        
        if not all_models:
            print("❌ No models found. Please ensure Ollama is running and models are installed.")
            return []
        
        print(f"📋 Found {len(all_models)} total models from Ollama")
        
        # Filter out ultra-large models
        filtered_models = filter_large_models(all_models)
        
        # Update global available models
        global available_models
        available_models = filtered_models
        
        # Display system optimization info
        if filtered_models:
            print(f"✅ {len(filtered_models)} models ready for use:")
            for i, model in enumerate(filtered_models, 1):
                print(f"   {i}. {model}")
            
            # Show system optimization
            info = model_manager.resource_manager.system_info
            optimal_concurrent, _ = model_manager.resource_manager.optimize_concurrent_models(filtered_models)
            
            print(f"\n🖥️  System: {info.available_ram_gb:.1f}GB RAM, {info.cpu_cores} CPU cores")
            if info.gpu_info:
                print(f"🎮 GPU: {len(info.gpu_info)} detected")
            print(f"⚡ Optimal concurrency: {optimal_concurrent} models")
            
            # Analyze model requirements
            model_manager.print_model_analysis(filtered_models[:5])  # Analyze first 5 models
        
        return filtered_models
        
    except Exception as e:
        print(f"❌ Error initializing models: {e}")
        return []

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
    """Get available models (filtered to exclude ultra-large models)."""
    global available_models
    
    # Use already filtered models, but refresh if empty
    if not available_models:
        available_models = filter_large_models(model_manager.get_available_models(force_refresh=True))
    
    coding_models = model_manager.get_models_for_question_type(QuestionType.CODING)
    # Also filter coding models
    coding_models = [m for m in coding_models if m in available_models]
    
    return jsonify({
        'success': True,
        'models': available_models,
        'coding_models': coding_models,
        'total_count': len(available_models),
        'coding_count': len(coding_models),
        'note': 'Ultra-large models (70B+ parameters) are filtered out for optimal performance'
    })

@app.route('/api/config')
def get_config():
    """Get current configuration."""
    return jsonify({
        'success': True,
        'config': config_manager.config
    })

@app.route('/api/system-info')
def get_system_info():
    """Get current system resource information."""
    try:
        info = model_manager.resource_manager.system_info
        optimal_concurrent, _ = model_manager.resource_manager.optimize_concurrent_models(
            model_manager.get_available_models()
        )
        
        return jsonify({
            'success': True,
            'ram': {
                'available': round(info.available_ram_gb, 1),
                'total': round(info.total_ram_gb, 1),
                'usage_percent': round((1 - info.available_ram_gb / info.total_ram_gb) * 100, 1)
            },
            'cpu_cores': info.cpu_cores,
            'gpus': info.gpu_info,  # Fixed: use gpu_info instead of gpus
            'optimal_concurrency': optimal_concurrent
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system-usage')
def get_system_usage():
    """Get real-time system resource usage."""
    try:
        usage_data = model_manager.resource_manager.get_real_time_usage()
        
        return jsonify({
            'success': True,
            'usage': usage_data,
            'timestamp': usage_data.get('timestamp', time.time())
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/models/refresh')
def refresh_models():
    """Refresh the model list from Ollama with filtering."""
    try:
        # Get all models from Ollama
        all_models = model_manager.get_available_models(force_refresh=True)
        
        # Filter out ultra-large models
        filtered_models = filter_large_models(all_models)
        
        # Update global available models
        global available_models
        available_models = filtered_models
        
        return jsonify({
            'success': True,
            'models': filtered_models,
            'count': len(filtered_models),
            'total_found': len(all_models),
            'filtered_count': len(all_models) - len(filtered_models),
            'timestamp': time.time(),
            'note': 'Ultra-large models (70B+ parameters) are automatically filtered out'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/models/analysis')
def get_model_analysis():
    """Get analysis of available models and system suitability."""
    try:
        models = model_manager.get_available_models()
        analysis = []
        
        total_estimated_ram = 0
        for model in models:
            model_info = model_manager.resource_manager.estimate_model_requirements(model)
            total_estimated_ram += model_info.min_ram_gb
            
            available_ram = model_manager.resource_manager.system_info.available_ram_gb
            
            if model_info.min_ram_gb > available_ram:
                status = 'critical'
            elif model_info.min_ram_gb > available_ram * 0.8:
                status = 'warning'
            else:
                status = 'good'
            
            analysis.append({
                'name': model,
                'size_gb': model_info.size_gb,
                'min_ram_gb': model_info.min_ram_gb,
                'recommended_ram_gb': model_info.recommended_ram_gb,
                'type': model_info.type,
                'status': status
            })
        
        available_ram = model_manager.resource_manager.system_info.available_ram_gb
        
        return jsonify({
            'success': True,
            'models': analysis,
            'summary': {
                'total_estimated_ram': round(total_estimated_ram, 1),
                'available_ram': round(available_ram, 1),
                'memory_pressure': 'high' if total_estimated_ram > available_ram * 0.8 
                                 else 'moderate' if total_estimated_ram > available_ram * 0.6 
                                 else 'low'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    
    # Initialize models on startup with filtering
    startup_models = initialize_models_on_startup()
    
    if not startup_models:
        print("⚠️  Warning: No models available. The application will start but functionality will be limited.")
        print("   Please ensure Ollama is running and models are installed.")
    
    print("\n🌐 Starting web server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
