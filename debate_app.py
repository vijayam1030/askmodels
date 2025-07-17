#!/usr/bin/env python3
"""
Model Debate Application
Flask-based web interface for multi-round model debates with streaming responses.
"""

import asyncio
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import threading
import queue
import time
import random

from models import (
    OllamaModelManager, 
    ConfigManager, 
    QuestionType, 
    PromptEnhancer,
    ModelResponse
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'debate-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
config_manager = ConfigManager()
model_manager = OllamaModelManager(config_manager)
available_models = []

# Debate configuration
DEBATE_ROUNDS = 3
MAX_DEBATE_MODELS = 4

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
    print("🔄 Initializing models for debate application...")
    
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
            print(f"✅ {len(filtered_models)} models ready for debates:")
            for i, model in enumerate(filtered_models, 1):
                print(f"   {i}. {model}")
            
            # Show system optimization
            info = model_manager.resource_manager.system_info
            optimal_concurrent, _ = model_manager.resource_manager.optimize_concurrent_models(filtered_models)
            
            print(f"\n🖥️  System: {info.available_ram_gb:.1f}GB RAM, {info.cpu_cores} CPU cores")
            if info.gpu_info:
                print(f"🎮 GPU: {len(info.gpu_info)} detected")
            print(f"⚡ Optimal concurrency: {optimal_concurrent} models")
            print(f"🗣️  Debate configuration: {DEBATE_ROUNDS} rounds, max {MAX_DEBATE_MODELS} participants")
        
        return filtered_models
        
    except Exception as e:
        print(f"❌ Error initializing models: {e}")
        return []

class DebateStreamingHandler:
    """Handles streaming responses for debate interface."""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.responses = {}
        self.start_times = {}
    
    async def streaming_callback(self, model_name: str, chunk: str, is_done: bool):
        """Callback for streaming model responses during debate."""
        if chunk and not is_done:
            # Initialize model tracking if first chunk
            if model_name not in self.responses:
                self.responses[model_name] = ""
                self.start_times[model_name] = time.time()
                socketio.emit('debate_model_started', {
                    'model': model_name,
                    'session_id': self.session_id
                })
            
            # Add chunk to response
            self.responses[model_name] += chunk
            
            # Emit chunk to client
            socketio.emit('debate_chunk_received', {
                'model': model_name,
                'chunk': chunk,
                'session_id': self.session_id
            })
            
        elif is_done:
            # Model completed
            elapsed_time = time.time() - self.start_times.get(model_name, 0)
            socketio.emit('debate_model_completed', {
                'model': model_name,
                'elapsed_time': elapsed_time,
                'session_id': self.session_id
            })

class DebateManager:
    """Manages the debate flow and rounds."""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.debate_history = []
        self.current_round = 0
        self.debate_models = []
        self.original_topic = ""
        
    def select_debate_models(self, available_models, count=None):
        """Select models for the debate."""
        if count is None:
            count = min(MAX_DEBATE_MODELS, len(available_models))
        
        # Select diverse models for better debate
        selected = random.sample(available_models, min(count, len(available_models)))
        self.debate_models = selected
        return selected
    
    def create_debate_prompt(self, topic, round_num, previous_arguments=None):
        """Create a prompt for the current debate round."""
        if round_num == 1:
            return f"""You are participating in a structured debate on the following topic:

TOPIC: {topic}

This is ROUND {round_num} of {DEBATE_ROUNDS}. Please present your initial position on this topic. 

Requirements:
- Present a clear, well-reasoned argument
- Take a specific stance (for, against, or nuanced position)
- Provide evidence or logical reasoning
- Be concise but thorough (2-3 paragraphs)
- Maintain a respectful, academic tone

Your argument:"""
        
        else:
            previous_args_text = "\n\n".join([
                f"**{arg['model']}** (Round {arg['round']}):\n{arg['content']}"
                for arg in previous_arguments[-len(self.debate_models):]  # Last round's arguments
            ])
            
            return f"""You are participating in a structured debate on the following topic:

TOPIC: {topic}

This is ROUND {round_num} of {DEBATE_ROUNDS}. 

PREVIOUS ARGUMENTS FROM ROUND {round_num-1}:
{previous_args_text}

Please respond to the previous arguments and present your position for this round.

Requirements:
- Address specific points made by other participants
- Strengthen your position or acknowledge valid opposing points
- Provide new evidence or reasoning
- Be concise but thorough (2-3 paragraphs)
- Maintain a respectful, academic tone

Your response:"""
    
    def create_summary_prompt(self, topic, all_arguments):
        """Create a prompt for the final summary."""
        debate_text = "\n\n".join([
            f"**{arg['model']}** (Round {arg['round']}):\n{arg['content']}"
            for arg in all_arguments
        ])
        
        return f"""You are tasked with providing a comprehensive summary and analysis of the following debate:

TOPIC: {topic}

COMPLETE DEBATE TRANSCRIPT:
{debate_text}

Please provide a final analysis that includes:

1. **Key Positions**: Summarize the main positions taken by participants
2. **Strongest Arguments**: Identify the most compelling arguments from each side
3. **Points of Agreement**: Note any areas where participants agreed
4. **Unresolved Issues**: Highlight remaining questions or disagreements
5. **Conclusion**: Provide a balanced assessment of the debate outcome

Format your response with clear sections and maintain objectivity. Do not declare a "winner" but rather synthesize the discussion into meaningful insights.

FINAL ANALYSIS:"""

@app.route('/')
def index():
    """Main page."""
    return render_template('debate.html')

@app.route('/api/models')
def get_models():
    """Get available models for debate."""
    global available_models
    
    # Use already filtered models, but refresh if empty
    if not available_models:
        available_models = filter_large_models(model_manager.get_available_models(force_refresh=True))
    
    return jsonify({
        'success': True,
        'models': available_models,
        'total_count': len(available_models),
        'max_debate_participants': MAX_DEBATE_MODELS,
        'debate_rounds': DEBATE_ROUNDS,
        'note': 'Ultra-large models (70B+ parameters) are filtered out for optimal performance'
    })

@app.route('/api/config')
def get_config():
    """Get current configuration."""
    return jsonify({
        'success': True,
        'config': config_manager.config,
        'debate_config': {
            'rounds': DEBATE_ROUNDS,
            'max_participants': MAX_DEBATE_MODELS
        }
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
            'gpus': info.gpu_info,
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

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Debate client connected: {request.sid}")
    emit('connected', {'session_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Debate client disconnected: {request.sid}")

@socketio.on('start_debate')
def handle_start_debate(data):
    """Handle debate start request."""
    topic = data.get('topic', '').strip()
    participant_count = data.get('participant_count', 3)
    session_id = request.sid
    
    if not topic:
        emit('error', {'message': 'Please provide a debate topic'})
        return
    
    if participant_count < 2 or participant_count > MAX_DEBATE_MODELS:
        emit('error', {'message': f'Participant count must be between 2 and {MAX_DEBATE_MODELS}'})
        return
    
    # Start processing in background
    thread = threading.Thread(
        target=process_debate_async,
        args=(topic, participant_count, session_id)
    )
    thread.daemon = True
    thread.start()

def process_debate_async(topic: str, participant_count: int, session_id: str):
    """Process debate asynchronously."""
    try:
        # Run in new event loop for thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            process_debate(topic, participant_count, session_id)
        )
        
        loop.close()
        
    except Exception as e:
        socketio.emit('error', {
            'message': f'Error processing debate: {str(e)}',
            'session_id': session_id
        })

async def process_debate(topic: str, participant_count: int, session_id: str):
    """Process the actual debate."""
    try:
        global available_models
        
        if not available_models:
            socketio.emit('error', {
                'message': 'No models available for debate',
                'session_id': session_id
            })
            return
        
        # Initialize debate manager
        debate_manager = DebateManager(session_id)
        debate_manager.original_topic = topic
        
        # Select debate participants
        selected_models = debate_manager.select_debate_models(available_models, participant_count)
        
        # Emit debate start
        socketio.emit('debate_started', {
            'topic': topic,
            'participants': selected_models,
            'rounds': DEBATE_ROUNDS,
            'session_id': session_id
        })
        
        # Conduct debate rounds
        for round_num in range(1, DEBATE_ROUNDS + 1):
            debate_manager.current_round = round_num
            
            socketio.emit('debate_round_started', {
                'round': round_num,
                'total_rounds': DEBATE_ROUNDS,
                'session_id': session_id
            })
            
            # Create prompt for this round
            prompt = debate_manager.create_debate_prompt(
                topic, 
                round_num, 
                debate_manager.debate_history
            )
            
            # Setup streaming handler
            streaming_handler = DebateStreamingHandler(session_id)
            
            # Query all participants for this round
            responses = await model_manager.query_multiple_models(
                selected_models,
                prompt,
                max_concurrent=min(3, len(selected_models)),
                stream=True,
                callback=streaming_handler.streaming_callback
            )
            
            # Store round results
            for response in responses:
                if response.is_successful():
                    debate_manager.debate_history.append({
                        'round': round_num,
                        'model': response.model_name,
                        'content': response.response,
                        'timestamp': time.time()
                    })
            
            # Emit round completion
            round_results = [
                {
                    'model': r.model_name,
                    'response': r.response,
                    'success': r.is_successful(),
                    'error': r.error if not r.is_successful() else None
                }
                for r in responses
            ]
            
            socketio.emit('debate_round_completed', {
                'round': round_num,
                'results': round_results,
                'session_id': session_id
            })
            
            # Brief pause between rounds
            if round_num < DEBATE_ROUNDS:
                await asyncio.sleep(2)
        
        # Generate final summary
        socketio.emit('debate_summary_started', {
            'session_id': session_id
        })
        
        # Use one of the participants to generate summary (or select best model)
        summary_model = selected_models[0]  # Could be improved to select best model
        summary_prompt = debate_manager.create_summary_prompt(topic, debate_manager.debate_history)
        
        summary_response = await model_manager.query_model(summary_model, summary_prompt, stream=False)
        
        # Emit final results
        socketio.emit('debate_completed', {
            'topic': topic,
            'participants': selected_models,
            'total_rounds': DEBATE_ROUNDS,
            'summary': {
                'model': summary_model,
                'content': summary_response.response if summary_response.is_successful() else "Error generating summary",
                'success': summary_response.is_successful()
            },
            'debate_history': debate_manager.debate_history,
            'session_id': session_id
        })
        
    except Exception as e:
        socketio.emit('error', {
            'message': f'Error during debate processing: {str(e)}',
            'session_id': session_id
        })

if __name__ == '__main__':
    print("🗣️  Starting Model Debate Application...")
    print("📡 Server will be available at: http://localhost:5001")
    
    # Initialize models on startup with filtering
    startup_models = initialize_models_on_startup()
    
    if not startup_models:
        print("⚠️  Warning: No models available. The application will start but functionality will be limited.")
        print("   Please ensure Ollama is running and models are installed.")
    
    print("\n🌐 Starting debate web server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
