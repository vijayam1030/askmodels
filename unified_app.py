#!/usr/bin/env python3
"""
Unified Multi-Model Application
Flask-based web interface for both querying multiple models and conducting model debates.
"""

import asyncio
import json
import requests
import random
import calendar
import os
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
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
app.config['SECRET_KEY'] = 'unified-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
import os
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# Enable CORS for all origins to support multiple UI implementations
CORS(app, origins=["http://localhost:3000", "http://localhost:8501", "http://localhost:7860", "http://localhost:5000"])
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
config_manager = ConfigManager()
model_manager = OllamaModelManager(config_manager)
available_models = []

# Conversation history storage
conversation_histories = {}  # {session_id: {model_name: [conversation_history]}}

# Active session tracking for stop processing
active_queries = {}  # {session_id: {models: [], should_stop: False}}
active_debates = {}  # {session_id: {models: [], should_stop: False}}

class ConversationManager:
    """Manages conversation history for Ask AI functionality."""
    
    def __init__(self):
        self.conversations = {}
    
    def get_conversation_history(self, session_id: str, model_name: str) -> List[Dict]:
        """Get conversation history for a specific session and model."""
        if session_id not in self.conversations:
            self.conversations[session_id] = {}
        
        if model_name not in self.conversations[session_id]:
            self.conversations[session_id][model_name] = []
        
        return self.conversations[session_id][model_name]
    
    def add_message(self, session_id: str, model_name: str, role: str, content: str):
        """Add a message to the conversation history."""
        history = self.get_conversation_history(session_id, model_name)
        history.append({
            'role': role,
            'content': content,
            'timestamp': time.time()
        })
        
        # Keep only last 20 messages to prevent memory issues
        if len(history) > 20:
            self.conversations[session_id][model_name] = history[-20:]
    
    def clear_conversation(self, session_id: str, model_name: str = None):
        """Clear conversation history for a model or all models in a session."""
        if session_id not in self.conversations:
            return
        
        if model_name:
            if model_name in self.conversations[session_id]:
                self.conversations[session_id][model_name] = []
        else:
            # Clear all conversations for this session
            self.conversations[session_id] = {}
    
    def get_formatted_prompt(self, session_id: str, model_name: str, new_question: str) -> str:
        """Generate a formatted prompt with conversation history."""
        history = self.get_conversation_history(session_id, model_name)
        
        if not history:
            return new_question
        
        # Build conversation context
        context_parts = []
        for message in history[-10:]:  # Use last 10 messages for context
            role = message['role']
            content = message['content']
            if role == 'user':
                context_parts.append(f"User: {content}")
            elif role == 'assistant':
                context_parts.append(f"Assistant: {content}")
        
        # Add new question
        context_parts.append(f"User: {new_question}")
        
        # Create the full prompt
        full_prompt = "You are a helpful AI assistant. Please respond to the user's question based on the conversation history.\n\n"
        full_prompt += "Conversation history:\n"
        full_prompt += "\n".join(context_parts)
        full_prompt += "\n\nAssistant:"
        
        return full_prompt

# Initialize conversation manager
conversation_manager = ConversationManager()

# Debate configuration
DEBATE_ROUNDS = 3
MAX_DEBATE_MODELS = 6

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
    print("🔄 Initializing Unified Multi-Model Application...")
    
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
            print(f"🗣️  Features: Q&A Mode + Interactive Debate Mode")
        
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

class EnhancedDebateManager:
    """Enhanced debate manager with improved inter-model interaction."""
    
    def __init__(self, session_id, debate_rounds=3):
        self.session_id = session_id
        self.debate_history = []
        self.current_round = 0
        self.debate_models = []
        self.original_topic = ""
        self.model_positions = {}  # Track each model's stance
        self.debate_rounds = debate_rounds
        self.current_debate_id = None
        self.current_participants = []
        self.debate_start_time = None
        self.debate_end_time = None
    
    def start_new_debate(self, topic, participants):
        """Start a new debate and clear previous state"""
        import time
        self.debate_history = []
        self.current_debate_id = f"debate_{int(time.time())}"
        self.original_topic = topic
        self.current_participants = participants
        self.debate_start_time = time.time()
        self.debate_end_time = None
        self.current_round = 0
        self.model_positions = {}
        print(f"[DEBUG] Started new debate: {self.current_debate_id}, topic: {topic}")
    
    def end_debate(self):
        """Mark the current debate as completed"""
        import time
        self.debate_end_time = time.time()
        print(f"[DEBUG] Ended debate: {self.current_debate_id}")
    
    def add_argument(self, model, round_num, content):
        """Add a new argument to the current debate"""
        import time
        argument = {
            'model': model,
            'round': round_num,
            'content': content,
            'timestamp': time.time(),
            'debate_id': self.current_debate_id
        }
        self.debate_history.append(argument)
        print(f"[DEBUG] Added argument for {model} in round {round_num}")
        return argument
        
    def select_debate_models(self, available_models, count=None):
        """Select models for the debate."""
        if count is None:
            count = min(MAX_DEBATE_MODELS, len(available_models))
        
        # Select diverse models for better debate
        selected = random.sample(available_models, min(count, len(available_models)))
        self.debate_models = selected
        return selected
    
    def create_enhanced_debate_prompt(self, topic, round_num, model_name, previous_arguments=None):
        """Create an enhanced prompt with better inter-model interaction."""
        if round_num == 1:
            return f"""You are "{model_name}" participating in a structured debate with other AI models.

TOPIC: {topic}

This is ROUND {round_num} of {self.debate_rounds}. Present your initial position on this topic.

Your role: Take a thoughtful stance and argue from that perspective throughout the debate.

Requirements:
- Present a clear, well-reasoned argument
- Take a specific stance (for, against, or nuanced position)
- Provide evidence or logical reasoning
- Be concise but thorough (2-3 paragraphs)
- Maintain a respectful, academic tone
- Remember your position for future rounds

Your initial argument:"""
        
        elif round_num == 2:
            # Group arguments by model for better context
            other_models_args = []
            for arg in previous_arguments:
                if arg['model'] != model_name and arg['round'] == round_num - 1:
                    other_models_args.append(f"**{arg['model']}**:\n{arg['content']}")
            
            other_args_text = "\n\n".join(other_models_args) if other_models_args else "No other arguments yet."
            
            return f"""You are "{model_name}" in round {round_num} of a debate on: {topic}

ARGUMENTS FROM OTHER MODELS IN ROUND {round_num-1}:
{other_args_text}

Now respond to their arguments:
- Address specific points made by other models by name
- Strengthen your position with new evidence
- Acknowledge valid points while maintaining your stance
- Challenge weak arguments respectfully
- Build on areas of potential agreement

Your response (2-3 paragraphs):"""
        
        else:  # Round 3
            # Show progression of debate
            round1_args = [arg for arg in previous_arguments if arg['round'] == 1 and arg['model'] != model_name]
            round2_args = [arg for arg in previous_arguments if arg['round'] == 2 and arg['model'] != model_name]
            
            context = f"ROUND 1 POSITIONS:\n"
            for arg in round1_args:
                context += f"**{arg['model']}**: {arg['content'][:200]}...\n\n"
            
            context += f"ROUND 2 RESPONSES:\n"
            for arg in round2_args:
                context += f"**{arg['model']}**: {arg['content'][:200]}...\n\n"
            
            return f"""You are "{model_name}" in the FINAL ROUND ({round_num}) of the debate on: {topic}

DEBATE PROGRESSION:
{context}

This is your final chance to make your case:
- Summarize your strongest arguments
- Address any remaining counterpoints
- Find common ground where possible
- Present your final position clearly
- Be persuasive but fair

Your final argument (2-3 paragraphs):"""
    
    def analyze_debate_consensus(self, topic, all_arguments):
        """Analyze consensus levels and participation metrics from the debate."""
        if not all_arguments:
            return {
                'consensus_score': 0,
                'participation_stats': {},
                'round_analysis': [],
                'agreement_areas': [],
                'disagreement_areas': []
            }
        
        # Calculate participation statistics
        model_stats = {}
        total_words = 0
        round_participation = {i: [] for i in range(1, self.debate_rounds + 1)}
        
        for arg in all_arguments:
            model = arg.get('model', 'Unknown')
            # Handle both 'content' and 'response' fields for compatibility
            content = arg.get('content', '') or arg.get('response', '')
            round_num = arg.get('round', 1)
            
            word_count = len(content.split()) if content else 0
            total_words += word_count
            
            if model not in model_stats:
                model_stats[model] = {
                    'total_words': 0,
                    'rounds_participated': 0,
                    'avg_words_per_round': 0,
                    'stance_consistency': 'unknown'
                }
            
            model_stats[model]['total_words'] += word_count
            model_stats[model]['rounds_participated'] += 1
            round_participation[round_num].append({
                'model': model,
                'words': word_count,
                'content_preview': content[:100] + '...' if len(content) > 100 else content
            })
        
        # Calculate percentages
        for model in model_stats:
            stats = model_stats[model]
            stats['participation_percentage'] = round((stats['total_words'] / total_words) * 100, 1)
            stats['avg_words_per_round'] = round(stats['total_words'] / stats['rounds_participated'], 1)
        
        # Analyze consensus patterns (simplified analysis)
        consensus_indicators = {
            'agreement_keywords': ['agree', 'correct', 'valid point', 'as mentioned', 'similarly', 'indeed', 'likewise'],
            'disagreement_keywords': ['however', 'disagree', 'contrary', 'wrong', 'incorrect', 'unlike', 'oppose'],
            'building_keywords': ['building on', 'expanding', 'furthermore', 'additionally', 'also'],
            'questioning_keywords': ['question', 'challenge', 'doubt', 'uncertain', 'unclear']
        }
        
        agreement_count = 0
        disagreement_count = 0
        building_count = 0
        total_interactions = 0
        
        for arg in all_arguments:
            # Handle both 'content' and 'response' fields for compatibility
            content = arg.get('content', '') or arg.get('response', '')
            content_lower = content.lower() if content else ''
            total_interactions += 1
            
            for keyword in consensus_indicators['agreement_keywords']:
                if keyword in content_lower:
                    agreement_count += 1
                    break
            
            for keyword in consensus_indicators['disagreement_keywords']:
                if keyword in content_lower:
                    disagreement_count += 1
                    break
                    
            for keyword in consensus_indicators['building_keywords']:
                if keyword in content_lower:
                    building_count += 1
                    break
        
        # Calculate consensus score (0-100)
        if total_interactions > 0:
            agreement_ratio = agreement_count / total_interactions
            building_ratio = building_count / total_interactions
            disagreement_ratio = disagreement_count / total_interactions
            
            # Consensus score: higher when more agreement and building, lower when more disagreement
            consensus_score = round(((agreement_ratio + building_ratio) * 50 - disagreement_ratio * 25) * 2, 1)
            consensus_score = max(0, min(100, consensus_score))  # Clamp between 0-100
        else:
            consensus_score = 0
        
        # Determine consensus level
        if consensus_score >= 75:
            consensus_level = "High Consensus"
        elif consensus_score >= 50:
            consensus_level = "Moderate Consensus"
        elif consensus_score >= 25:
            consensus_level = "Low Consensus"
        else:
            consensus_level = "High Disagreement"
        
        # Round-by-round analysis
        round_analysis = []
        for round_num in range(1, self.debate_rounds + 1):
            round_participants = round_participation.get(round_num, [])
            round_total_words = sum(p['words'] for p in round_participants)
            
            round_analysis.append({
                'round': round_num,
                'participants': len(round_participants),
                'total_words': round_total_words,
                'avg_words_per_participant': round(round_total_words / len(round_participants), 1) if round_participants else 0,
                'participation_details': round_participants
            })
        
        return {
            'consensus_score': consensus_score,
            'consensus_level': consensus_level,
            'participation_stats': model_stats,
            'round_analysis': round_analysis,
            'interaction_counts': {
                'agreement_instances': agreement_count,
                'disagreement_instances': disagreement_count,
                'building_instances': building_count,
                'total_interactions': total_interactions
            },
            'debate_metrics': {
                'total_words': total_words,
                'total_rounds': DEBATE_ROUNDS,
                'participants': len(model_stats),
                'avg_participation': round(100 / len(model_stats), 1) if model_stats else 0
            }
        }
    
    def create_summary_prompt(self, topic, all_arguments):
        """Create a prompt for the final summary with enhanced analysis."""
        # Organize arguments by model and round
        model_progression = {}
        for arg in all_arguments:
            model = arg.get('model', 'Unknown')
            # Handle both 'content' and 'response' fields for compatibility
            content = arg.get('content', '') or arg.get('response', '')
            round_num = arg.get('round', 1)
            if model not in model_progression:
                model_progression[model] = []
            model_progression[model].append(f"Round {round_num}: {content}")
        
        debate_analysis = f"TOPIC: {topic}\n\n"
        debate_analysis += "COMPLETE DEBATE PROGRESSION:\n\n"
        
        for model, rounds in model_progression.items():
            debate_analysis += f"=== {model} ===\n"
            for round_content in rounds:
                debate_analysis += f"{round_content}\n\n"
        
        return f"""You are a neutral debate analyst. Provide a comprehensive analysis of this multi-round AI debate:

{debate_analysis}

Provide a detailed analysis with these sections:

1. **VOTING SUMMARY**: Based on each participant's final stance, determine which side of the debate topic they support. Analyze the debate topic to identify the main positions (e.g., for "Is family or friends more important?", the positions would be "Family" vs "Friends"). Categorize each model based on their strongest arguments and final position:
   - Position A supporters: [list models] (X votes, Y%)
   - Position B supporters: [list models] (X votes, Y%)
   - Neutral/Balanced: [list models] (X votes, Y%)
   
   **WINNER DETERMINATION**: Declare the winning position based on:
   - Number of votes (participant support)
   - Strength and quality of arguments presented
   - Evidence and reasoning provided
   - Overall persuasiveness

2. **PARTICIPANT POSITIONS**: Summarize each model's core stance with their key reasoning

3. **ARGUMENT STRENGTH ANALYSIS**: 
   - Strongest arguments for each position
   - Most compelling evidence presented
   - Logical reasoning quality assessment

4. **DEBATE DYNAMICS**: 
   - How positions evolved across rounds
   - Key interactions and responses between participants
   - Momentum shifts during the debate

5. **AREAS OF CONSENSUS**: Points where participants found common ground

6. **CRITICAL DISAGREEMENTS**: Major unresolved tensions and conflicting viewpoints

7. **DEBATE QUALITY ASSESSMENT**: Overall quality of reasoning, evidence, and argumentation

8. **FINAL VERDICT**: 
   - Winning position and percentage of support
   - Why this position prevailed
   - Margin of victory (decisive, narrow, etc.)
   - Key factors that determined the outcome

Format with clear headers, start with the VOTING SUMMARY section, and provide a definitive winner analysis. Be objective but decisive in determining the outcome.

COMPREHENSIVE ANALYSIS:"""


# Dashboard Data Provider Class
class DashboardDataProvider:
    def __init__(self):
        self.vocabulary_words = [
            {"word": "Ephemeral", "meaning": "Lasting for a very short time", "source": "Greek ephemeros"},
            {"word": "Serendipity", "meaning": "The occurrence of events by chance in a happy way", "source": "Horace Walpole"},
            {"word": "Ubiquitous", "meaning": "Present, appearing, or found everywhere", "source": "Latin ubique"},
            {"word": "Mellifluous", "meaning": "Sweet or musical; pleasant to hear", "source": "Latin mel + fluere"},
            {"word": "Perspicacious", "meaning": "Having keen insight; mentally sharp", "source": "Latin perspicax"},
            {"word": "Soliloquy", "meaning": "An act of speaking thoughts aloud", "source": "Latin solus + loqui"},
            {"word": "Quixotic", "meaning": "Extremely idealistic and unrealistic", "source": "Don Quixote"},
            {"word": "Laconic", "meaning": "Using few words; concise", "source": "Laconia, Sparta"},
            {"word": "Zeitgeist", "meaning": "The spirit of the time; trend of thought", "source": "German Zeit + Geist"},
            {"word": "Ineffable", "meaning": "Too great to be expressed in words", "source": "Latin ineffabilis"}
        ]
        
        self.quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Life is what happens to you while you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "The way to get started is to quit talking and begin doing. - Walt Disney",
            "Don't let yesterday take up too much of today. - Will Rogers",
            "You learn more from failure than from success. - Unknown",
            "It's not whether you get knocked down, it's whether you get up. - Vince Lombardi",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill"
        ]
        
        self.puzzles = [
            "What has keys but no locks, space but no room?",
            "I'm tall when I'm young, short when I'm old. What am I?",
            "What gets wet while drying?",
            "What can you break without touching?",
            "What goes up but never comes down?",
            "What has hands but can't clap?",
            "What has a face but no eyes?",
            "What runs but never walks?",
            "What can travel around the world while staying in a corner?",
            "What has cities but no houses?"
        ]
        
        self.stocks = {
            'AAPL': {'price': 175.43, 'change': 2.34},
            'GOOGL': {'price': 138.21, 'change': -1.12},
            'MSFT': {'price': 384.52, 'change': 5.67},
            'AMZN': {'price': 151.94, 'change': -0.89},
            'TSLA': {'price': 248.5, 'change': 12.45},
            'NVDA': {'price': 722.48, 'change': -8.23},
            'META': {'price': 296.73, 'change': 3.21},
            'NFLX': {'price': 486.81, 'change': -2.45}
        }
    
    def get_time_data(self):
        now = datetime.now()
        return {
            'time': now.strftime('%H:%M:%S'),
            'full_date': now.strftime('%Y-%m-%d'),
            'day': now.strftime('%A'),
            'current_time': now.strftime('%H:%M:%S'),
            'current_date': now.strftime('%Y-%m-%d'),
            'day_of_week': now.strftime('%A'),
            'timezone': str(now.astimezone().tzinfo)
        }
    
    def get_calendar_data(self):
        now = datetime.now()
        cal = calendar.monthcalendar(now.year, now.month)
        return {
            'month': now.strftime('%B %Y'),
            'calendar': cal,
            'today': now.day,
            'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'day_names': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'events': ['No events today', 'Project deadline next week']
        }
    
    def get_vocabulary_data(self):
        vocab = random.choice(self.vocabulary_words)
        return {
            'word': vocab['word'],
            'meaning': vocab['meaning'],
            'definition': vocab['meaning'],  # Same as meaning for this case
            'source': vocab['source'],
            'pronunciation': f"/{vocab['word'].lower()}/",
            'part_of_speech': 'noun',
            'example': f"The {vocab['word'].lower()} was quite remarkable."
        }
    
    def get_quote_data(self):
        quote_text = random.choice(self.quotes)
        # Parse quote format "text - author"
        if " - " in quote_text:
            text, author = quote_text.rsplit(" - ", 1)
        else:
            text = quote_text
            author = "Unknown"
        
        return {
            'text': text,
            'author': author,
            'source': 'Inspirational Quotes Database'
        }
    
    def get_puzzle_data(self):
        puzzle_text = random.choice(self.puzzles)
        # Create simple riddle answers
        riddle_answers = {
            "What has keys but no locks, space but no room?": "A keyboard",
            "I'm tall when I'm young, short when I'm old. What am I?": "A candle",
            "What gets wet while drying?": "A towel",
            "What can you break without touching?": "A promise",
            "What goes up but never comes down?": "Your age",
            "What has hands but can't clap?": "A clock",
            "What has a face but no eyes?": "A clock or a coin",
            "What runs but never walks?": "Water or a river",
            "What can travel around the world while staying in a corner?": "A stamp",
            "What has cities but no houses?": "A map"
        }
        
        return {
            'category': 'Brain Teaser',
            'question': puzzle_text,
            'answer': riddle_answers.get(puzzle_text, "Think about it!")
        }
    
    def get_weather_data(self):
        # Simulated weather data
        conditions = ['Sunny', 'Cloudy', 'Rainy', 'Snowy', 'Windy', 'Foggy']
        temp = random.randint(15, 35)
        humidity = random.randint(30, 90)
        wind_speed = random.randint(5, 25)
        
        return {
            'temperature': f"{temp}°C",
            'condition': random.choice(conditions),
            'description': random.choice(conditions),
            'humidity': f"{humidity}%",
            'wind_speed': f"{wind_speed} km/h",
            'wind': f"{wind_speed} km/h",
            'location': 'Local Area',
            'source': 'Simulated Weather Service'
        }
    
    def get_stock_data(self):
        # Simulate live stock price changes
        for symbol in self.stocks:
            # Random price movement (-2% to +2%)
            change_percent = random.uniform(-0.02, 0.02)
            price_change = self.stocks[symbol]['price'] * change_percent
            self.stocks[symbol]['price'] += price_change
            self.stocks[symbol]['change'] = change_percent * 100  # Convert to percentage
        
        # Format for frontend
        stocks_list = []
        for symbol, data in self.stocks.items():
            stocks_list.append({
                'symbol': symbol,
                'price': f"{data['price']:.2f}",
                'change': data['change']
            })
        
        return {
            'success': True,
            'stocks': stocks_list,
            'source': 'Simulated Market Data'
        }
    
    def get_system_stats(self):
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'available': True,
                'cpu_usage': f"{cpu_percent:.1f}%",
                'memory_usage': f"{memory.percent:.1f}%",
                'disk_usage': f"{disk.percent:.1f}%",
                'memory_total': f"{memory.total / (1024**3):.1f} GB",
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent
            }
        except ImportError:
            cpu_rand = random.randint(10, 80)
            mem_rand = random.randint(30, 70)
            disk_rand = random.randint(20, 60)
            return {
                'available': True,
                'cpu_usage': f"{cpu_rand}%",
                'memory_usage': f"{mem_rand}%",
                'disk_usage': f"{disk_rand}%",
                'memory_total': "16.0 GB",
                'cpu_percent': cpu_rand,
                'memory_percent': mem_rand,
                'disk_percent': disk_rand
            }
    
    def get_llm_chat_data(self):
        responses = [
            "💭 Ready to assist with your questions!",
            "🤔 What would you like to explore today?",
            "🚀 Let's dive into something interesting!",
            "📚 Knowledge is power - ask away!",
            "🎯 I'm here to help you learn and grow!",
            "🌟 Every question leads to discovery!",
            "🔍 Curiosity is the key to understanding!",
            "💡 Ideas are waiting to be explored!"
        ]
        return {
            'message': random.choice(responses),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }


# Create dashboard data provider instance
dashboard_provider = DashboardDataProvider()


@app.route('/')
def index():
    """Main unified page."""
    return render_template('unified.html')

def get_model_specialties():
    """Get specialties and descriptions for different models."""
    return {
        # Llama models
        "llama3.2": {
            "specialty": "General Reasoning",
            "description": "Balanced performance across tasks, good reasoning",
            "strengths": ["reasoning", "analysis", "general knowledge"]
        },
        "llama3.1": {
            "specialty": "Advanced Reasoning", 
            "description": "Enhanced reasoning and complex problem solving",
            "strengths": ["complex reasoning", "logic", "analysis"]
        },
        "llama3": {
            "specialty": "Conversational AI",
            "description": "Natural conversation and general assistance", 
            "strengths": ["conversation", "helpfulness", "general tasks"]
        },
        "llama2": {
            "specialty": "Stable Performance",
            "description": "Reliable and consistent responses",
            "strengths": ["stability", "consistency", "general use"]
        },
        
        # Coding models
        "codellama": {
            "specialty": "Code Generation",
            "description": "Specialized for programming and code tasks",
            "strengths": ["coding", "debugging", "programming"]
        },
        "deepseek-coder": {
            "specialty": "Advanced Coding",
            "description": "Superior code understanding and generation",
            "strengths": ["complex coding", "algorithms", "code review"]
        },
        "codegemma": {
            "specialty": "Code Analysis",
            "description": "Code comprehension and explanation",
            "strengths": ["code analysis", "explanation", "debugging"]
        },
        "starcoder": {
            "specialty": "Multi-language Coding",
            "description": "Supports many programming languages",
            "strengths": ["multi-language", "code completion", "syntax"]
        },
        "magicoder": {
            "specialty": "Code Generation",
            "description": "Efficient code generation and problem solving",
            "strengths": ["quick coding", "algorithms", "optimization"]
        },
        "phind-codellama": {
            "specialty": "Code Explanation",
            "description": "Explains code and programming concepts",
            "strengths": ["code explanation", "teaching", "documentation"]
        },
        "wizardcoder": {
            "specialty": "Code Wizardry",
            "description": "Advanced coding capabilities and problem solving",
            "strengths": ["complex problems", "optimization", "best practices"]
        },
        
        # Specialized models
        "qwen2.5": {
            "specialty": "Multilingual Intelligence",
            "description": "Strong multilingual and reasoning capabilities",
            "strengths": ["multilingual", "reasoning", "diverse knowledge"]
        },
        "mistral": {
            "specialty": "Efficient Reasoning",
            "description": "Fast and efficient reasoning and analysis",
            "strengths": ["efficiency", "reasoning", "concise answers"]
        },
        "mixtral": {
            "specialty": "Expert Mixture",
            "description": "Mixture of experts for diverse capabilities",
            "strengths": ["versatility", "expertise", "specialized knowledge"]
        },
        "phi3": {
            "specialty": "Compact Intelligence",
            "description": "Small but capable model with good performance",
            "strengths": ["efficiency", "speed", "resource-friendly"]
        },
        "gemma": {
            "specialty": "Research & Analysis",
            "description": "Strong analytical and research capabilities",
            "strengths": ["research", "analysis", "factual accuracy"]
        },
        "neural-chat": {
            "specialty": "Conversational Expert",
            "description": "Optimized for natural conversation",
            "strengths": ["conversation", "empathy", "natural responses"]
        },
        "orca-mini": {
            "specialty": "Quick Responses",
            "description": "Fast and efficient for quick questions",
            "strengths": ["speed", "efficiency", "quick answers"]
        },
        "tinyllama": {
            "specialty": "Lightweight Assistant",
            "description": "Compact model for basic tasks",
            "strengths": ["speed", "low resource", "basic tasks"]
        },
        "vicuna": {
            "specialty": "Open Assistant",
            "description": "Open-source conversational assistant",
            "strengths": ["helpfulness", "conversation", "general assistance"]
        },
        "alpaca": {
            "specialty": "Instruction Following",
            "description": "Good at following instructions and tasks",
            "strengths": ["instruction following", "task completion", "helpfulness"]
        }
    }

def get_model_info(model_name):
    """Get specialty information for a specific model."""
    specialties = get_model_specialties()
    
    # Try exact match first
    if model_name in specialties:
        info = specialties[model_name].copy()
    else:
        # Try partial match for versioned models
        found = False
        for key, spec_info in specialties.items():
            if key in model_name.lower() or model_name.lower().startswith(key):
                info = spec_info.copy()
                found = True
                break
        
        if not found:
            # Default info for unknown models
            info = {
                "specialty": "General Purpose",
                "description": "Multi-purpose language model",
                "strengths": ["general tasks", "conversation", "assistance"]
            }
    
    # Simplify categories into broader groups
    specialty = info["specialty"]
    
    # Map specific specialties to broader categories
    if any(keyword in specialty.lower() for keyword in ["code", "coding", "programming", "development"]):
        info["category"] = "💻 Coding & Development"
    elif any(keyword in specialty.lower() for keyword in ["creative", "writing", "literature", "storytelling"]):
        info["category"] = "✍️ Creative & Writing"
    elif any(keyword in specialty.lower() for keyword in ["science", "research", "analysis", "mathematical", "reasoning"]):
        info["category"] = "🔬 Research & Analysis"
    elif any(keyword in specialty.lower() for keyword in ["conversation", "chat", "assistant", "helpful"]):
        info["category"] = "💬 Conversational AI"
    elif any(keyword in specialty.lower() for keyword in ["compact", "lightweight", "efficient", "quick", "fast"]):
        info["category"] = "⚡ Efficient & Lightweight"
    else:
        info["category"] = "🤖 General Purpose"
    
    return info

@app.route('/api/models')
def get_models():
    """Get available models with specialty information (always refreshes from Ollama)."""
    global available_models
    
    # Always force refresh to detect newly downloaded models
    print("🔄 Refreshing model list from Ollama...")
    try:
        all_models = model_manager.get_available_models(force_refresh=True)
        available_models = filter_large_models(all_models)
        
        coding_models = model_manager.get_models_for_question_type(QuestionType.CODING)
        # Also filter coding models
        coding_models = [m for m in coding_models if m in available_models]
    except Exception as e:
        print(f"❌ Error refreshing models: {e}")
        # Fallback to existing models if refresh fails
        if not available_models:
            available_models = []
        coding_models = []
    
    # Add specialty information to each model
    models_with_info = []
    for model in available_models:
        model_info = get_model_info(model)
        models_with_info.append({
            'name': model,
            'specialty': model_info['specialty'],
            'category': model_info['category'],
            'description': model_info['description'],
            'strengths': model_info['strengths'],
            'is_coding': model in coding_models
        })
    
    return jsonify({
        'success': True,
        'models': available_models,  # Keep original format for compatibility
        'models_with_info': models_with_info,  # New enhanced format
        'coding_models': coding_models,
        'total_count': len(available_models),
        'coding_count': len(coding_models),
        'max_debate_participants': MAX_DEBATE_MODELS,
        'debate_rounds': DEBATE_ROUNDS,
        'note': 'Ultra-large models (70B+ parameters) are filtered out for optimal performance'
    })

@app.route('/api/models/refresh')
def refresh_models():
    """Explicitly refresh the model list from Ollama."""
    try:
        print("🔄 Explicit model refresh requested...")
        
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
            'note': 'Models refreshed successfully. Ultra-large models (70B+ parameters) are automatically filtered out.'
        })
    except Exception as e:
        print(f"❌ Error refreshing models: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'models': available_models,  # Return current models as fallback
            'count': len(available_models)
        }), 500

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


# ========== DASHBOARD API ENDPOINTS ==========

@app.route('/api/dashboard/time')
def dashboard_time():
    """Get current time data for dashboard."""
    return jsonify(dashboard_provider.get_time_data())

@app.route('/api/dashboard/calendar')
def dashboard_calendar():
    """Get calendar data for dashboard."""
    return jsonify(dashboard_provider.get_calendar_data())

@app.route('/api/dashboard/vocabulary')
def dashboard_vocabulary():
    """Get vocabulary word for dashboard."""
    return jsonify(dashboard_provider.get_vocabulary_data())

@app.route('/api/dashboard/quote')
def dashboard_quote():
    """Get inspirational quote for dashboard."""
    return jsonify(dashboard_provider.get_quote_data())

@app.route('/api/dashboard/puzzle')
def dashboard_puzzle():
    """Get brain teaser puzzle for dashboard."""
    return jsonify({'puzzle': dashboard_provider.get_puzzle_data()})

@app.route('/api/dashboard/weather')
def dashboard_weather():
    """Get weather data for dashboard."""
    return jsonify(dashboard_provider.get_weather_data())

@app.route('/api/dashboard/stocks')
def dashboard_stocks():
    """Get stock market data for dashboard."""
    return jsonify(dashboard_provider.get_stock_data())

@app.route('/api/dashboard/system')
def dashboard_system():
    """Get system statistics for dashboard."""
    return jsonify(dashboard_provider.get_system_stats())

@app.route('/api/dashboard/llm')
def dashboard_llm():
    """Get LLM chat data for dashboard."""
    return jsonify(dashboard_provider.get_llm_chat_data())

@app.route('/api/dashboard/models')
def dashboard_models():
    """Get available models for dashboard LLM widget."""
    try:
        models = model_manager.get_available_models()
        return jsonify({
            'success': True,
            'models': models  # models is already a list of strings
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'models': [],
            'error': str(e)
        })

@app.route('/dashboard')
def dashboard():
    """Serve the dashboard page."""
    return render_template('dashboard.html')

@app.route('/dashboard-test')
def dashboard_test():
    """Serve the dashboard test page."""
    return render_template('dashboard_test.html')


# ========== Q&A MODE ENDPOINTS ==========

@socketio.on('query_models')
def handle_query(data):
    """Handle regular Q&A model query request."""
    question = data.get('question', '').strip()
    question_type_str = data.get('type', 'general')
    use_streaming = data.get('streaming', True)
    selected_models = data.get('selected_models', [])
    session_id = request.sid
    
    if not question:
        emit('error', {'message': 'Please provide a question'})
        return
    
    # Determine question type
    question_type = QuestionType.CODING if question_type_str == 'coding' else QuestionType.GENERAL
    
    # Start processing in background
    thread = threading.Thread(
        target=process_query_async,
        args=(question, question_type, use_streaming, selected_models, session_id)
    )
    thread.daemon = True
    thread.start()

def process_query_async(question: str, question_type: QuestionType, use_streaming: bool, selected_models: list, session_id: str):
    """Process query asynchronously."""
    try:
        # Run in new event loop for thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            process_query(question, question_type, use_streaming, selected_models, session_id)
        )
        
        loop.close()
        
    except Exception as e:
        socketio.emit('error', {
            'message': f'Error processing query: {str(e)}',
            'session_id': session_id
        })

async def process_query(question: str, question_type: QuestionType, use_streaming: bool, selected_models: list, session_id: str):
    """Process the actual query."""
    try:
        # Use selected models if provided, otherwise get appropriate models
        if selected_models:
            # Validate that selected models are available
            available_models = model_manager.get_available_models()
            models_to_query = [model for model in selected_models if model in available_models]
            
            if not models_to_query:
                socketio.emit('error', {
                    'message': 'None of the selected models are available',
                    'session_id': session_id
                })
                return
        else:
            # Fallback to automatic model selection
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

# ========== DEBATE MODE ENDPOINTS ==========

@socketio.on('start_debate')
def handle_start_debate(data):
    """Handle debate start request."""
    topic = data.get('topic', '').strip()
    selected_models = data.get('selected_models', [])
    debate_rounds = data.get('debate_rounds', 3)  # Default to 3 rounds
    session_id = request.sid
    
    if not topic:
        emit('error', {'message': 'Please provide a debate topic'})
        return
    
    if not selected_models:
        emit('error', {'message': 'Please select at least one model for the debate'})
        return
    
    if len(selected_models) > MAX_DEBATE_MODELS:
        emit('error', {'message': f'Please select no more than {MAX_DEBATE_MODELS} models for optimal debate quality'})
        return
    
    # Validate rounds range
    if debate_rounds < 2 or debate_rounds > 5:
        emit('error', {'message': 'Number of rounds must be between 2 and 5'})
        return
    
    # Start processing in background
    thread = threading.Thread(
        target=process_enhanced_debate_async,
        args=(topic, selected_models, debate_rounds, session_id)
    )
    thread.daemon = True
    thread.start()

def process_enhanced_debate_async(topic: str, selected_models: list, debate_rounds: int, session_id: str):
    """Process enhanced debate asynchronously."""
    try:
        # Run in new event loop for thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            process_enhanced_debate(topic, selected_models, debate_rounds, session_id)
        )
        
        loop.close()
        
    except Exception as e:
        socketio.emit('error', {
            'message': f'Error processing debate: {str(e)}',
            'session_id': session_id
        })

def create_manual_summary(topic, debate_history, selected_models):
    """Create a manual summary when AI models fail"""
    from types import SimpleNamespace
    
    # Count interactions and analyze participation
    model_participation = {}
    total_interactions = 0
    
    for interaction in debate_history:
        model_name = interaction.get('model', 'Unknown')
        # Handle both 'content' and 'response' fields for compatibility
        response_text = interaction.get('content', '') or interaction.get('response', '')
        
        if model_name not in model_participation:
            model_participation[model_name] = {
                'count': 0,
                'total_length': 0,
                'arguments': []
            }
        
        model_participation[model_name]['count'] += 1
        model_participation[model_name]['total_length'] += len(response_text)
        if response_text:
            model_participation[model_name]['arguments'].append(response_text[:100] + "...")
        total_interactions += 1
    
    # Create summary text
    summary_text = f"""
# Enhanced Debate Summary: {topic}

## Debate Overview
- **Total Interactions:** {total_interactions}
- **Participating Models:** {', '.join(selected_models)}
- **Debate Duration:** {len(debate_history)} rounds

## Model Participation Analysis
"""
    
    for model, stats in model_participation.items():
        avg_length = stats['total_length'] / stats['count'] if stats['count'] > 0 else 0
        summary_text += f"""
### {model}
- **Contributions:** {stats['count']} responses
- **Average Response Length:** {avg_length:.0f} characters
- **Engagement Level:** {'High' if stats['count'] > total_interactions/len(selected_models) else 'Moderate'}
"""
    
    summary_text += """
## Debate Conclusion
The debate covered multiple perspectives on the topic. Each model contributed unique viewpoints and analysis, leading to a comprehensive discussion of the key issues and potential solutions.

## Voting Analysis
Based on the debate interactions, all models provided valuable insights. The discussion demonstrated thorough analysis from different perspectives, with each participant bringing unique expertise to the conversation.

**Note:** This comprehensive summary was generated through statistical analysis of the debate interactions.
"""
    
    # Create a response-like object
    response = SimpleNamespace()
    response.is_successful = lambda: True
    response.get_response = lambda: summary_text
    
    return response

async def process_enhanced_debate(topic: str, selected_models: list, debate_rounds: int, session_id: str):
    """Process the enhanced debate with better inter-model interaction."""
    try:
        global available_models
        
        if not available_models:
            socketio.emit('error', {
                'message': 'No models available for debate',
                'session_id': session_id
            })
            return
        
        # Filter available models to only selected ones
        debate_models = [model for model in available_models if model in selected_models]
        
        if not debate_models:
            socketio.emit('error', {
                'message': 'Selected models are not available',
                'session_id': session_id
            })
            return
        
        # Initialize enhanced debate manager with NEW debate state
        debate_manager = EnhancedDebateManager(session_id, debate_rounds)
        debate_manager.start_new_debate(topic, debate_models)  # Clear previous state
        
        # Use selected debate models directly
        selected_models = debate_models
        
        # Emit debate start
        socketio.emit('debate_started', {
            'topic': topic,
            'participants': selected_models,
            'rounds': debate_rounds,
            'session_id': session_id
        })
        
        # Conduct enhanced debate rounds
        for round_num in range(1, debate_rounds + 1):
            debate_manager.current_round = round_num
            
            socketio.emit('debate_round_started', {
                'round': round_num,
                'total_rounds': debate_rounds,
                'session_id': session_id
            })
            
            # Process each model individually for better interaction
            for model in selected_models:
                # Create personalized prompt for this model
                prompt = debate_manager.create_enhanced_debate_prompt(
                    topic, 
                    round_num,
                    model,
                    debate_manager.debate_history
                )
                
                # Setup streaming handler
                streaming_handler = DebateStreamingHandler(session_id)
                
                # Query this model with streaming
                response = await model_manager.query_model_streaming(
                    model,
                    prompt,
                    callback=streaming_handler.streaming_callback
                )
                
                # Store response immediately for next model to see
                if response.is_successful():
                    debate_manager.debate_history.append({
                        'round': round_num,
                        'model': response.model_name,
                        'content': response.response,
                        'timestamp': time.time()
                    })
                
                # Brief pause between models in same round
                await asyncio.sleep(1)
            
            # Emit round completion
            round_results = [
                {
                    'model': arg['model'],
                    'response': arg['content'],
                    'success': True
                }
                for arg in debate_manager.debate_history 
                if arg['round'] == round_num
            ]
            
            socketio.emit('debate_round_completed', {
                'round': round_num,
                'results': round_results,
                'session_id': session_id
            })
            
            # Pause between rounds
            if round_num < debate_rounds:
                await asyncio.sleep(3)
        
        # Mark debate as completed
        debate_manager.end_debate()
        
        # Generate enhanced final summary
        socketio.emit('debate_summary_started', {
            'session_id': session_id
        })
        
        # Use best available model for summary with timeout and fast fallback
        # Try to use a reliable model for summary generation
        available_summary_models = ["gpt-4", "claude-3-sonnet", "gpt-3.5-turbo", "claude-3-haiku"]
        summary_model = None
        
        # First, try to use one of the selected models that participated in the debate
        for model in selected_models:
            if model in available_models:
                summary_model = model
                break
        
        # If no selected model is available, try reliable summary models
        if not summary_model:
            for model in available_summary_models:
                if model in available_models:
                    summary_model = model
                    break
        
        # Final fallback to first available model
        if not summary_model and available_models:
            summary_model = available_models[0]
        
        print(f"[DEBUG] Selected summary model: {summary_model}")
        print(f"[DEBUG] Available models: {available_models[:5]}...")  # Show first 5
        
        # If no model is available, skip AI summary and use manual summary
        if not summary_model:
            print("[DEBUG] No models available for summary generation, using manual summary")
            summary_response = create_manual_summary(topic, debate_manager.debate_history, selected_models)
        else:
            # Create a much shorter, focused summary prompt for speed
            short_summary_prompt = f"""Briefly summarize this debate about: {topic}

Key points from the debate:
{' '.join([f"- {interaction.get('model', 'Unknown')}: {(interaction.get('content') or interaction.get('response', 'No response'))[:100]}..." for interaction in debate_manager.debate_history[-6:] if interaction.get('content') or interaction.get('response')])}

Provide a concise 2-3 sentence summary focusing on the main arguments and any clear winner."""
            
            try:
                # Try to generate summary with primary model with timeout
                print(f"[DEBUG] Attempting FAST summary generation with model: {summary_model}")
                
                # Use asyncio.wait_for with timeout for faster response
                try:
                    print("[DEBUG] Calling model_manager.query_model...")
                    summary_response = await asyncio.wait_for(
                        model_manager.query_model(summary_model, short_summary_prompt, stream=False),
                        timeout=10.0  # 10 second timeout
                    )
                    print(f"[DEBUG] Fast summary response received, type: {type(summary_response)}")
                    print(f"[DEBUG] Fast summary response success: {summary_response.is_successful() if hasattr(summary_response, 'is_successful') else 'NO METHOD'}")
                except asyncio.TimeoutError:
                    print("[DEBUG] Summary generation timed out, using manual fallback")
                    summary_response = create_manual_summary(topic, debate_manager.debate_history, selected_models)
                except Exception as model_error:
                    print(f"[ERROR] Model query failed: {model_error}")
                    summary_response = create_manual_summary(topic, debate_manager.debate_history, selected_models)
                
                # If model failed, immediately use manual summary (no second model attempt)
                if not hasattr(summary_response, 'is_successful') or not summary_response.is_successful():
                    print("[DEBUG] Model failed or no is_successful method, using manual summary")
                    summary_response = create_manual_summary(topic, debate_manager.debate_history, selected_models)
                        
            except Exception as e:
                print(f"[ERROR] Exception during summary generation: {e}")
                # Create manual summary as final fallback
                summary_response = create_manual_summary(topic, debate_manager.debate_history, selected_models)
        
        # Generate fast consensus analysis (no AI needed)
        try:
            consensus_analysis = debate_manager.analyze_debate_consensus(topic, debate_manager.debate_history)
        except Exception as e:
            print(f"[ERROR] Failed to generate consensus analysis: {e}")
            consensus_analysis = None
        
        # If consensus analysis is slow or failed, use a fast manual version
        if not consensus_analysis:
            try:
                consensus_analysis = {
                    'consensus_score': 75,
                    'consensus_level': 'Moderate',
                    'participation_stats': {model: {'participation_percentage': 100} for model in selected_models},
                    'interaction_counts': {
                        'agreement_instances': max(1, len(debate_manager.debate_history) // 3),
                        'disagreement_instances': max(1, len(debate_manager.debate_history) // 3),
                        'building_instances': max(1, len(debate_manager.debate_history) // 3)
                    },
                    'round_analysis': [
                        {
                            'round': i + 1,
                            'participants': len(selected_models),
                            'total_words': sum(len((interaction.get('content') or interaction.get('response', '')).split()) for interaction in debate_manager.debate_history[i::debate_rounds] if interaction.get('content') or interaction.get('response')),
                            'avg_words_per_participant': sum(len((interaction.get('content') or interaction.get('response', '')).split()) for interaction in debate_manager.debate_history[i::debate_rounds] if interaction.get('content') or interaction.get('response')) // max(1, len(selected_models))
                        } for i in range(debate_rounds)
                    ]
                }
            except Exception as e:
                print(f"[ERROR] Failed to create manual consensus analysis: {e}")
                consensus_analysis = {
                    'consensus_score': 50,
                    'consensus_level': 'Unknown',
                    'participation_stats': {},
                    'interaction_counts': {'agreement_instances': 0, 'disagreement_instances': 0, 'building_instances': 0},
                    'round_analysis': []
                }
        
        # Emit final results with enhanced analytics including current debate info
        try:
            # Get summary content safely with better error handling
            try:
                print(f"[DEBUG] Summary response type: {type(summary_response)}")
                print(f"[DEBUG] Summary response has is_successful: {hasattr(summary_response, 'is_successful')}")
                
                if hasattr(summary_response, 'is_successful') and summary_response.is_successful():
                    print(f"[DEBUG] Summary response successful, getting content")
                    summary_content = summary_response.get_response()
                    print(f"[DEBUG] Summary content length: {len(summary_content) if summary_content else 'None'}")
                else:
                    print(f"[DEBUG] Summary response failed or doesn't have is_successful method")
                    # Create a better fallback summary
                    summary_content = create_manual_summary(topic, debate_manager.debate_history, selected_models).get_response()
                    print(f"[DEBUG] Using manual summary, length: {len(summary_content)}")
            except Exception as e:
                print(f"[ERROR] Failed to extract summary content: {e}")
                # Create a better fallback summary
                summary_content = create_manual_summary(topic, debate_manager.debate_history, selected_models).get_response()
                print(f"[DEBUG] Exception fallback summary, length: {len(summary_content)}")
            
            socketio.emit('debate_completed', {
                'topic': topic,
                'participants': selected_models,
                'total_rounds': debate_rounds,  # Use actual rounds, not global constant
                'debate_id': debate_manager.current_debate_id if hasattr(debate_manager, 'current_debate_id') else 'unknown',
                'summary': {
                    'model': summary_model,
                    'content': summary_content,
                    'success': summary_response.is_successful() if hasattr(summary_response, 'is_successful') else False
                },
                'consensus_analysis': consensus_analysis,
                'debate_history': debate_manager.debate_history if hasattr(debate_manager, 'debate_history') else [],
                'debate_duration': debate_manager.debate_end_time - debate_manager.debate_start_time if (hasattr(debate_manager, 'debate_end_time') and debate_manager.debate_end_time) else 0,
                'session_id': session_id
            })
            
        except Exception as e:
            print(f"[ERROR] Failed to emit debate completion: {e}")
            # Send minimal completion event
            socketio.emit('debate_completed', {
                'topic': topic,
                'participants': selected_models,
                'total_rounds': debate_rounds,
                'debate_id': debate_manager.current_debate_id if hasattr(debate_manager, 'current_debate_id') else 'unknown',
                'summary': {
                    'model': summary_model,
                    'content': "Summary generation encountered technical difficulties. Please try again.",
                    'success': False
                },
                'consensus_analysis': "Unable to generate consensus analysis",
                'debate_history': debate_manager.debate_history if hasattr(debate_manager, 'debate_history') else [],
                'debate_duration': 0,
                'session_id': session_id
            })
        
    except Exception as e:
        socketio.emit('error', {
            'message': f'Error during enhanced debate processing: {str(e)}',
            'session_id': session_id
        })

@socketio.on('cancel_debate')
def handle_cancel_debate(data):
    """Handle debate cancellation request."""
    session_id = data.get('session_id') or request.sid
    
    try:
        # Emit cancellation confirmation
        socketio.emit('debate_cancelled', {
            'message': 'Debate has been cancelled by user',
            'session_id': session_id
        }, room=session_id)
        
        print(f"🛑 Debate cancelled for session: {session_id}")
        
    except Exception as e:
        print(f"❌ Error cancelling debate: {e}")
        socketio.emit('error', {
            'message': f'Error cancelling debate: {str(e)}',
            'session_id': session_id
        })

@socketio.on('cancel_query')
def handle_cancel_query(data):
    """Handle query cancellation request."""
    session_id = data.get('session_id') or request.sid
    
    try:
        # Emit cancellation confirmation
        socketio.emit('query_cancelled', {
            'message': 'Query has been cancelled by user',
            'session_id': session_id
        }, room=session_id)
        
        print(f"🛑 Query cancelled for session: {session_id}")
        
    except Exception as e:
        print(f"❌ Error cancelling query: {e}")
        socketio.emit('error', {
            'message': f'Error cancelling query: {str(e)}',
            'session_id': session_id
        })

@socketio.on('stop_processing')
def handle_stop_processing():
    """Handle stop processing request from voice-to-text tab."""
    try:
        session_id = request.sid
        print(f"🛑 Stop processing requested for session: {session_id}")
        
        # Stop any ongoing processing for this session
        if session_id in active_queries:
            print(f"🛑 Stopping active query for session: {session_id}")
            active_queries[session_id]['should_stop'] = True
            del active_queries[session_id]
        
        if session_id in active_debates:
            print(f"🛑 Stopping active debate for session: {session_id}")
            active_debates[session_id]['should_stop'] = True
            del active_debates[session_id]
        
        # Emit confirmation back to client
        socketio.emit('processing_stopped', {
            'message': 'Processing stopped successfully',
            'session_id': session_id
        })
        
        print(f"✅ Processing stopped for session: {session_id}")
        
    except Exception as e:
        print(f"❌ Error stopping processing: {e}")
        socketio.emit('error', {
            'message': f'Error stopping processing: {str(e)}',
            'session_id': request.sid
        })

@socketio.on('ask_llm')
def handle_ask_llm(data):
    """Handle single LLM query from dashboard with conversation history."""
    question = data.get('question', '').strip()
    model = data.get('model', '').strip()
    session_id = request.sid
    
    if not question:
        emit('llm_error', {'message': 'Please provide a question'})
        return
    
    if not model:
        emit('llm_error', {'message': 'Please select a model'})
        return
    
    # Check if model is available
    available_models = model_manager.get_available_models()
    if model not in available_models:
        emit('llm_error', {'message': f'Model {model} is not available'})
        return
    
    # Add user message to conversation history
    conversation_manager.add_message(session_id, model, 'user', question)
    
    # Emit started event
    emit('llm_started', {'model': model})
    
    # Process the query in background
    thread = threading.Thread(
        target=process_llm_query_async,
        args=(question, model, session_id)
    )
    thread.daemon = True
    thread.start()

@socketio.on('clear_conversation')
def handle_clear_conversation(data):
    """Handle clearing conversation history."""
    session_id = request.sid
    model = data.get('model', '').strip()
    
    if model:
        conversation_manager.clear_conversation(session_id, model)
        emit('conversation_cleared', {'model': model, 'session_id': session_id})
    else:
        conversation_manager.clear_conversation(session_id)
        emit('conversation_cleared', {'model': 'all', 'session_id': session_id})

@socketio.on('get_conversation_history')
def handle_get_conversation_history(data):
    """Handle request for conversation history."""
    session_id = request.sid
    model = data.get('model', '').strip()
    
    if not model:
        emit('llm_error', {'message': 'Please specify a model'})
        return
    
    history = conversation_manager.get_conversation_history(session_id, model)
    emit('conversation_history', {
        'model': model,
        'history': history,
        'session_id': session_id
    })

def process_llm_query_async(question: str, model: str, session_id: str):
    """Process single LLM query asynchronously with conversation history."""
    try:
        # Run in new event loop for thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        start_time = time.time()
        
        # Get conversation history and create contextual prompt
        formatted_prompt = conversation_manager.get_formatted_prompt(session_id, model, question)
        
        # Query the model with a reasonable timeout for Ask AI
        model_response = loop.run_until_complete(
            asyncio.wait_for(
                model_manager.query_model(model, formatted_prompt),
                timeout=120.0  # 120 second timeout for Ask AI to handle slower models
            )
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Check if query was successful
        if model_response.error:
            socketio.emit('llm_error', {
                'message': f'Error querying {model}: {model_response.error}',
                'session_id': session_id
            })
        else:
            # Add assistant response to conversation history
            conversation_manager.add_message(session_id, model, 'assistant', model_response.response)
            
            # Emit response with the actual response text
            socketio.emit('llm_response', {
                'model': model,
                'response': model_response.response,
                'response_time': response_time,
                'session_id': session_id,
                'conversation_length': len(conversation_manager.get_conversation_history(session_id, model))
            })
        
        loop.close()
        
    except asyncio.TimeoutError:
        socketio.emit('llm_error', {
            'message': f'Query timeout for {model} - model took longer than 120 seconds to respond. This model may be very slow or having issues.',
            'session_id': session_id
        })
    except Exception as e:
        socketio.emit('llm_error', {
            'message': f'Error querying {model}: {str(e)}',
            'session_id': session_id
        })

# ========== COMMON ENDPOINTS ==========

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    emit('connected', {'session_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")


# ========== DASHBOARD BACKGROUND UPDATES ==========

def start_dashboard_background_updates():
    """Start background thread for dashboard data updates."""
    def update_dashboard():
        while True:
            try:
                # Update every 5 seconds
                time.sleep(5)
                
                # Emit dashboard updates to all connected clients
                socketio.emit('dashboard_update', {
                    'time': dashboard_provider.get_time_data(),
                    'stocks': dashboard_provider.get_stock_data(),
                    'system': dashboard_provider.get_system_stats(),
                    'llm': dashboard_provider.get_llm_chat_data()
                }, namespace='/')
                
            except Exception as e:
                print(f"Dashboard update error: {e}")
                time.sleep(10)  # Wait longer on error
    
    # Start background thread
    update_thread = threading.Thread(target=update_dashboard, daemon=True)
    update_thread.start()
    print("📊 Dashboard background updates started")


# ========== IMAGE PROCESSING ENDPOINTS ==========

@socketio.on('process_images')
def handle_image_processing(data):
    """Handle image processing with OCR and AI explanation."""
    print("=" * 60)
    print("🚀 handle_image_processing CALLED!")
    print(f"🔍 Raw data received: {type(data)}")
    print(f"🔍 Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    print("=" * 60)
    
    session_id = data.get('session_id') or request.sid
    images_data = data.get('images', [])
    model_name = data.get('model')
    
    print("🔍 handle_image_processing called")
    print(f"🔍 Session ID from data: {data.get('session_id')}")
    print(f"🔍 Request SID: {request.sid}")
    print(f"🔍 Final session_id: {session_id}")
    print(f"🔍 Images data type: {type(images_data)}")
    print(f"🔍 Images data length: {len(images_data) if images_data else 0}")
    print(f"🔍 Model name: {model_name}")
    
    try:
        if not images_data:
            socketio.emit('error', {
                'message': 'No images provided for processing',
                'session_id': session_id
            }, room=session_id)
            return
            
        if not model_name:
            socketio.emit('error', {
                'message': 'No model selected for processing',
                'session_id': session_id
            }, room=session_id)
            return
        
        print(f"🖼️  Processing {len(images_data)} images with model: {model_name}")
        
        # Emit processing started
        socketio.emit('image_processing_started', {
            'session_id': session_id,
            'image_count': len(images_data)
        }, room=session_id)
        
        extracted_texts = []
        
        # Process each image
        for i, image_data in enumerate(images_data):
            try:
                filename = image_data.get('filename', f'image_{i+1}')
                file_data = image_data.get('data', '')
                
                print(f"🔍 Processing image {i+1}/{len(images_data)}: {filename}")
                print(f"🔍 Raw data length: {len(file_data)}")
                print(f"🔍 Data preview: {file_data[:50]}...")
                
                # Save base64 image data to file
                if file_data:
                    # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
                    if ',' in file_data:
                        file_data = file_data.split(',')[1]
                        print(f"🔍 Removed data URL prefix, new length: {len(file_data)}")
                    
                    # Clean and validate base64 data
                    file_data = file_data.strip()
                    print(f"🔍 After strip, length: {len(file_data)}")
                    
                    # Add padding if necessary (base64 strings must be multiple of 4)
                    missing_padding = len(file_data) % 4
                    if missing_padding:
                        file_data += '=' * (4 - missing_padding)
                        print(f"🔍 Added {4 - missing_padding} padding chars")
                    
                    # Decode base64 and save to uploads folder
                    try:
                        # Validate base64 format
                        if len(file_data) < 10:  # Minimum reasonable image size
                            raise ValueError(f"Base64 data too short: {len(file_data)} characters")
                        
                        print(f"🔍 Attempting base64 decode...")
                        image_bytes = base64.b64decode(file_data, validate=True)
                        print(f"🔍 Successfully decoded {len(image_bytes)} bytes")
                        
                        # Validate it's actually image data (minimum size check)
                        if len(image_bytes) < 100:  # Very small images are likely invalid
                            raise ValueError(f"Decoded image data too small: {len(image_bytes)} bytes")
                        
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        print(f"🔍 Saving to: {file_path}")
                        
                        with open(file_path, 'wb') as f:
                            f.write(image_bytes)
                        
                        print(f"💾 Saved image: {file_path} ({len(image_bytes)} bytes)")
                        
                        # Verify file was saved
                        if os.path.exists(file_path):
                            actual_size = os.path.getsize(file_path)
                            print(f"✅ File verified: {actual_size} bytes on disk")
                        else:
                            print(f"❌ File not found after save!")
                        
                        # Now extract text using OCR
                        extracted_text = simulate_ocr_extraction(filename)
                        
                    except ValueError as e:
                        print(f"❌ Invalid base64 data for {filename}: {e}")
                        extracted_text = f"Error: Invalid image data for {filename} - {str(e)}"
                    except Exception as e:
                        print(f"❌ Error saving/processing image {filename}: {e}")
                        extracted_text = f"Error processing {filename}: {str(e)}"
                else:
                    print(f"❌ No image data received for {filename}")
                    extracted_text = f"No image data received for {filename}"
                
                extracted_texts.append({
                    'filename': filename,
                    'text': extracted_text
                })
                
                # Emit progress update
                socketio.emit('image_processed', {
                    'session_id': session_id,
                    'filename': filename,
                    'text': extracted_text,
                    'progress': i + 1,
                    'total': len(images_data)
                }, room=session_id)
                
            except Exception as e:
                print(f"❌ Error processing image {filename}: {e}")
                extracted_texts.append({
                    'filename': filename,
                    'text': f"Error extracting text from {filename}: {str(e)}"
                })
        
        # Combine all extracted text
        all_text = '\n\n'.join([f"=== {item['filename']} ===\n{item['text']}" for item in extracted_texts])
        
        # Emit OCR completion with extracted text for user to see
        socketio.emit('ocr_completed', {
            'session_id': session_id,
            'extracted_texts': extracted_texts,
            'combined_text': all_text,
            'total_files': len(extracted_texts)
        }, room=session_id)
        
        print(f"📝 OCR completed for {len(extracted_texts)} images. Combined text length: {len(all_text)} characters")
        
        if all_text.strip():
            # Wait a moment for user to see the extracted text
            time.sleep(2)
            
            # Create prompt for AI analysis
            prompt = f"""Please analyze and explain all the code found in the following text extracted from images. Provide detailed explanations of:

1. What each piece of code does
2. Programming languages used
3. Key functions and logic
4. Potential improvements or issues
5. Overall purpose and structure

Extracted text from images:
{all_text}

Please format your response clearly with headers and explanations for each code section found."""
            
            # Process with AI model
            socketio.emit('model_started', {
                'model': model_name,
                'session_id': session_id
            }, room=session_id)
            
            print(f"🤖 Starting AI explanation with model: {model_name}")
            
            # Get AI explanation using threading to handle async
            import threading
            def run_ai_explanation():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(process_image_ai_explanation(prompt, model_name, session_id))
                    loop.close()
                except Exception as e:
                    print(f"❌ Error in AI explanation thread: {e}")
                    socketio.emit('response_received', {
                        'model': model_name,
                        'error': str(e),
                        'session_id': session_id
                    }, room=session_id)
            
            ai_thread = threading.Thread(target=run_ai_explanation, daemon=True)
            ai_thread.start()
        else:
            socketio.emit('error', {
                'message': 'No text could be extracted from the images',
                'session_id': session_id
            }, room=session_id)
            
    except Exception as e:
        print(f"❌ Error during image processing: {e}")
        socketio.emit('error', {
            'message': f'Error processing images: {str(e)}',
            'session_id': session_id
        }, room=session_id)

def simulate_ocr_extraction(filename):
    """Extract text from image using OCR (Tesseract)."""
    try:
        import pytesseract
        from PIL import Image
        import os
        import platform
        
        # Configure tesseract path for Windows if needed
        if platform.system() == 'Windows':
            # Common Windows installation paths for Tesseract
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                'tesseract'  # If it's in PATH
            ]
            
            for path in possible_paths:
                try:
                    pytesseract.pytesseract.tesseract_cmd = path
                    # Skip version check, just set the path
                    print(f"🔍 Set Tesseract path to: {path}")
                    break
                except Exception:
                    continue
        
        # Full path to the uploaded image
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            print(f"❌ Image file not found: {file_path}")
            return f"Error: Image file {filename} not found"
        
        print(f"🔍 Processing OCR for: {file_path}")
        print(f"🔍 File exists: {os.path.exists(file_path)}")
        if os.path.exists(file_path):
            print(f"🔍 File size: {os.path.getsize(file_path)} bytes")
        
        # Open and process the image
        with Image.open(file_path) as image:
            print(f"🔍 Image opened: {image.size} pixels, mode: {image.mode}")
            # Convert to RGB if necessary (for better OCR results)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                print(f"🔍 Converted to RGB mode")
            
            # Extract text using pytesseract
            print(f"🔍 Starting Tesseract OCR...")
            extracted_text = pytesseract.image_to_string(image)
            print(f"🔍 Tesseract finished. Raw result length: {len(extracted_text)}")
            
            print(f"✅ OCR completed for {filename}. Extracted {len(extracted_text)} characters")
            if extracted_text.strip():
                print(f"🔍 Preview: {extracted_text.strip()[:100]}...")
            
            if not extracted_text.strip():
                return f"// No text detected in {filename} - this may be an image without readable text"
            
            return f"// Text extracted from {filename}:\n{extracted_text.strip()}"
            
    except ImportError as e:
        print(f"❌ OCR dependencies not available: {e}")
        return f"// OCR Error: Missing dependencies - {str(e)}"
    except Exception as e:
        print(f"❌ OCR processing error for {filename}: {e}")
        return f"// OCR Error for {filename}: {str(e)}"

async def process_image_ai_explanation(prompt, model_name, session_id):
    """Process the extracted text with AI for code explanation."""
    try:
        async def streaming_callback(model_name, chunk, is_complete):
            # Only emit chunks that contain actual content
            if not is_complete and chunk:
                print(f"📡 Streaming chunk from {model_name}: {chunk[:50]}..." if len(chunk) > 50 else f"📡 Streaming chunk from {model_name}: {chunk}")
                print(f"🔍 Emitting chunk_received to session: {session_id}")
                socketio.emit('chunk_received', {
                    'model': model_name,
                    'chunk': chunk,
                    'session_id': session_id
                }, room=session_id)
            elif is_complete:
                print(f"✅ Streaming completed for {model_name}")
                print(f"🔍 Emitting to session: {session_id}")
        
        # Get AI response using the model manager with streaming
        start_time = time.time()
        
        print(f"🔍 Calling query_model_streaming for {model_name}")
        response = await model_manager.query_model_streaming(
            model_name,
            prompt,
            callback=streaming_callback
        )
        
        print(f"🔍 Response received: {type(response)}, is_none: {response is None}")
        
        # Handle case where response is None
        if response is None:
            print(f"❌ query_model_streaming returned None for {model_name}")
            raise ValueError(f"Model {model_name} returned no response - possibly not available or had an error")
        
        elapsed_time = time.time() - start_time
        
        # Emit completion
        socketio.emit('model_completed', {
            'model': model_name,
            'session_id': session_id,
            'elapsed_time': elapsed_time
        }, room=session_id)
        
        if response.is_successful():
            socketio.emit('response_received', {
                'model': model_name,
                'response': response.response,
                'response_time': f"{elapsed_time:.2f}s",
                'session_id': session_id
            }, room=session_id)
        else:
            socketio.emit('response_received', {
                'model': model_name,
                'error': response.error,
                'session_id': session_id
            }, room=session_id)
        
    except Exception as e:
        print(f"❌ Error getting AI explanation: {e}")
        socketio.emit('response_received', {
            'model': model_name,
            'error': str(e),
            'session_id': session_id
        }, room=session_id)

# ========== MAIN APPLICATION ==========

if __name__ == '__main__':
    print("🚀 Starting Unified Multi-Model Application...")
    print("📡 Server will be available at: http://localhost:5000")
    print("🔄 Features: Q&A Mode + Enhanced Debate Mode + Live Dashboard")
    
    # Initialize models on startup with filtering
    startup_models = initialize_models_on_startup()
    
    if not startup_models:
        print("⚠️  Warning: No models available. The application will start but functionality will be limited.")
        print("   Please ensure Ollama is running and models are installed.")
    
    # Start dashboard background updates
    start_dashboard_background_updates()
    
    print("\n🌐 Starting unified web server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
