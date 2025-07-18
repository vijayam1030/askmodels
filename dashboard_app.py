#!/usr/bin/env python3
"""
Live Dashboard Application
A comprehensive dashboard with time, calendar, quotes, puzzles, and LLM interaction.
"""

import asyncio
import json
import requests
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
import calendar

from models import OllamaModelManager, ConfigManager, QuestionType

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dashboard-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
config_manager = ConfigManager()
model_manager = OllamaModelManager(config_manager)

class DashboardDataProvider:
    """Provides data for dashboard widgets."""
    
    def __init__(self):
        self.current_quote = None
        self.current_puzzle = None
        self.puzzle_timer = 0
        self.quote_timer = 0
        
    def get_time_data(self):
        """Get current time with multiple formats."""
        now = datetime.now()
        return {
            'time': now.strftime('%H:%M:%S'),
            'date': now.strftime('%Y-%m-%d'),
            'day': now.strftime('%A'),
            'full_date': now.strftime('%B %d, %Y'),
            'timestamp': now.timestamp()
        }
    
    def get_calendar_data(self):
        """Get calendar data for current month."""
        now = datetime.now()
        cal = calendar.monthcalendar(now.year, now.month)
        
        # Get events for today (you can extend this to include real events)
        today_events = [
            "Dashboard monitoring active",
            "System health check",
        ]
        
        return {
            'month': now.strftime('%B %Y'),
            'calendar': cal,
            'today': now.day,
            'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'events': today_events
        }
    
    def get_philosophy_quote(self):
        """Get philosophy quote from free API."""
        try:
            # Using quotable.io - free philosophy quotes API
            response = requests.get('https://api.quotable.io/random?tags=philosophy', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'text': data.get('content', 'The unexamined life is not worth living.'),
                    'author': data.get('author', 'Socrates'),
                    'source': 'quotable.io'
                }
        except Exception as e:
            print(f"Quote API error: {e}")
        
        # Fallback quotes
        fallback_quotes = [
            {"text": "The only true wisdom is in knowing you know nothing.", "author": "Socrates"},
            {"text": "I think, therefore I am.", "author": "René Descartes"},
            {"text": "The unexamined life is not worth living.", "author": "Socrates"},
            {"text": "To be is to be perceived.", "author": "George Berkeley"},
            {"text": "Man is condemned to be free.", "author": "Jean-Paul Sartre"},
            {"text": "The greatest happiness of the greatest number is the foundation of morals and legislation.", "author": "Jeremy Bentham"},
            {"text": "What we know is a drop, what we don't know is an ocean.", "author": "Isaac Newton"},
            {"text": "The mind is everything. What you think you become.", "author": "Buddha"}
        ]
        
        quote = random.choice(fallback_quotes)
        quote['source'] = 'built-in'
        return quote
    
    def get_daily_puzzle(self):
        """Get a daily puzzle or brain teaser."""
        puzzles = [
            {
                "type": "riddle",
                "question": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?",
                "answer": "An echo",
                "category": "Classic Riddle"
            },
            {
                "type": "math",
                "question": "If you multiply me by any other number, the answer will always be the same. What number am I?",
                "answer": "Zero",
                "category": "Math Puzzle"
            },
            {
                "type": "logic",
                "question": "A man lives on the 20th floor of an apartment building. Every morning he takes the elevator down to the ground floor. When he comes home, he takes the elevator to the 10th floor and walks the rest of the way... except on rainy days, when he takes the elevator all the way up. Why?",
                "answer": "He's too short to reach the button for the 20th floor, except when he has an umbrella",
                "category": "Logic Puzzle"
            },
            {
                "type": "word",
                "question": "What word becomes shorter when you add two letters to it?",
                "answer": "Short (becomes 'shorter')",
                "category": "Word Play"
            },
            {
                "type": "riddle",
                "question": "The more you take, the more you leave behind. What am I?",
                "answer": "Footsteps",
                "category": "Classic Riddle"
            },
            {
                "type": "math",
                "question": "I am an odd number. Take away a letter and I become even. What number am I?",
                "answer": "Seven (remove 's' to get 'even')",
                "category": "Math Wordplay"
            },
            {
                "type": "logic",
                "question": "You are in a room with 3 light switches. Each switch controls a bulb in another room. You can only visit the other room once. How do you determine which switch controls which bulb?",
                "answer": "Turn on the first switch for a few minutes, then turn it off. Turn on the second switch. When you enter the room, the bulb that's on is controlled by switch 2, the warm bulb by switch 1, and the cool bulb by switch 3.",
                "category": "Logic Puzzle"
            },
            {
                "type": "riddle",
                "question": "What has keys but no locks, space but no room, and you can enter but not go inside?",
                "answer": "A keyboard",
                "category": "Modern Riddle"
            }
        ]
        
        return random.choice(puzzles)
    
    def get_vocabulary_word(self):
        """Get an interesting English word with definition, pronunciation, and example."""
        vocabulary_words = [
            {
                "word": "Serendipity",
                "pronunciation": "/ˌser·ənˈdɪp·ə·t̬i/",
                "part_of_speech": "noun",
                "definition": "The occurrence and development of events by chance in a happy or beneficial way.",
                "example": "A fortunate stroke of serendipity brought the two old friends together at the airport.",
                "etymology": "From the Persian fairy tale 'The Three Princes of Serendip'"
            },
            {
                "word": "Ephemeral",
                "pronunciation": "/ɪˈfem·ər·əl/",
                "part_of_speech": "adjective",
                "definition": "Lasting for a very short time; transitory.",
                "example": "The beauty of cherry blossoms is ephemeral, lasting only a few weeks each spring.",
                "etymology": "From Greek ephēmeros meaning 'lasting only a day'"
            },
            {
                "word": "Mellifluous",
                "pronunciation": "/məˈlɪf·lu·əs/",
                "part_of_speech": "adjective", 
                "definition": "Sweet or musical; pleasant to hear.",
                "example": "The mellifluous tones of the jazz singer captivated the entire audience.",
                "etymology": "From Latin mel (honey) + fluere (to flow)"
            },
            {
                "word": "Perspicacious",
                "pronunciation": "/ˌpɜr·spɪˈkeɪ·ʃəs/",
                "part_of_speech": "adjective",
                "definition": "Having a ready insight into and understanding of things; astute.",
                "example": "Her perspicacious analysis of the market trends helped the company avoid significant losses.",
                "etymology": "From Latin perspicax meaning 'sharp-sighted'"
            },
            {
                "word": "Ubiquitous",
                "pronunciation": "/juˈbɪk·wə·təs/",
                "part_of_speech": "adjective",
                "definition": "Present, appearing, or found everywhere.",
                "example": "Smartphones have become ubiquitous in modern society, found in nearly every pocket.",
                "etymology": "From Latin ubique meaning 'everywhere'"
            },
            {
                "word": "Luminous",
                "pronunciation": "/ˈlu·mə·nəs/",
                "part_of_speech": "adjective",
                "definition": "Full of or shedding light; bright or shining; inspiring and enlightening.",
                "example": "The luminous explanation made the complex scientific concept easy to understand.",
                "etymology": "From Latin lumen meaning 'light'"
            },
            {
                "word": "Resilience",
                "pronunciation": "/rɪˈzɪl·jəns/",
                "part_of_speech": "noun",
                "definition": "The ability to recover quickly from difficulties; mental or emotional strength.",
                "example": "The team showed remarkable resilience after losing their star player to injury.",
                "etymology": "From Latin resilire meaning 'to spring back'"
            },
            {
                "word": "Eloquent",
                "pronunciation": "/ˈel·ə·kwənt/",
                "part_of_speech": "adjective",
                "definition": "Fluent or persuasive in speaking or writing; clearly expressing or indicating something.",
                "example": "Her eloquent speech about climate change moved the audience to action.",
                "etymology": "From Latin eloqui meaning 'to speak out'"
            },
            {
                "word": "Ineffable",
                "pronunciation": "/ɪnˈef·ə·bəl/",
                "part_of_speech": "adjective",
                "definition": "Too great or extreme to be expressed or described in words.",
                "example": "The ineffable beauty of the sunset left everyone speechless.",
                "etymology": "From Latin ineffabilis meaning 'unutterable'"
            },
            {
                "word": "Quintessential",
                "pronunciation": "/ˌkwɪn·təˈsen·ʃəl/",
                "part_of_speech": "adjective",
                "definition": "Representing the most perfect or typical example of a quality or class.",
                "example": "The cozy bookshop with its wooden shelves and reading nooks was quintessential charm.",
                "etymology": "From Latin quinta essentia meaning 'fifth essence'"
            }
        ]
        
        word_data = random.choice(vocabulary_words)
        word_data['source'] = 'curated collection'
        return word_data
    
    def get_weather_data(self):
        """Get weather information (using a free API)."""
        try:
            # Using wttr.in for simple weather (no API key needed)
            response = requests.get('https://wttr.in/?format=j1', timeout=5)
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                return {
                    'temperature': f"{current['temp_C']}°C / {current['temp_F']}°F",
                    'description': current['weatherDesc'][0]['value'],
                    'humidity': f"{current['humidity']}%",
                    'wind': f"{current['windspeedKmph']} km/h",
                    'source': 'wttr.in'
                }
        except Exception as e:
            print(f"Weather API error: {e}")
        
        return {
            'temperature': 'N/A',
            'description': 'Weather data unavailable',
            'humidity': 'N/A',
            'wind': 'N/A',
            'source': 'offline'
        }
    
    def get_system_stats(self):
        """Get basic system statistics."""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent if psutil.disk_usage('/') else 0,
                'available': True
            }
        except ImportError:
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'available': False
            }

# Global data provider
data_provider = DashboardDataProvider()

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/dashboard/time')
def get_time():
    """Get current time data."""
    return jsonify(data_provider.get_time_data())

@app.route('/api/dashboard/calendar')
def get_calendar():
    """Get calendar data."""
    return jsonify(data_provider.get_calendar_data())

@app.route('/api/dashboard/quote')
def get_quote():
    """Get philosophy quote."""
    quote = data_provider.get_philosophy_quote()
    return jsonify(quote)

@app.route('/api/dashboard/vocabulary')
def get_vocabulary():
    """Get vocabulary word with definition."""
    vocab = data_provider.get_vocabulary_word()
    return jsonify(vocab)

@app.route('/api/dashboard/puzzle')
def get_puzzle():
    """Get daily puzzle."""
    puzzle = data_provider.get_daily_puzzle()
    return jsonify(puzzle)

@app.route('/api/dashboard/weather')
def get_weather():
    """Get weather data."""
    weather = data_provider.get_weather_data()
    return jsonify(weather)

@app.route('/api/dashboard/system')
def get_system():
    """Get system statistics."""
    stats = data_provider.get_system_stats()
    return jsonify(stats)

@app.route('/api/dashboard/models')
def get_models():
    """Get available LLM models."""
    try:
        models = model_manager.get_available_models()
        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'models': [],
            'count': 0
        })

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Dashboard client connected: {request.sid}")
    emit('connected', {'session_id': request.sid})

@socketio.on('ask_llm')
def handle_llm_query(data):
    """Handle LLM query request."""
    question = data.get('question', '').strip()
    model_name = data.get('model', '')
    session_id = request.sid
    
    if not question:
        emit('llm_error', {'message': 'Please provide a question'})
        return
    
    if not model_name:
        emit('llm_error', {'message': 'Please select a model'})
        return
    
    # Start processing in background
    thread = threading.Thread(
        target=process_llm_query_async,
        args=(question, model_name, session_id)
    )
    thread.daemon = True
    thread.start()

def process_llm_query_async(question: str, model_name: str, session_id: str):
    """Process LLM query asynchronously."""
    try:
        # Run in new event loop for thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            process_llm_query(question, model_name, session_id)
        )
        
        loop.close()
        
    except Exception as e:
        socketio.emit('llm_error', {
            'message': f'Error processing query: {str(e)}',
            'session_id': session_id
        })

async def process_llm_query(question: str, model_name: str, session_id: str):
    """Process the LLM query."""
    try:
        # Emit query start
        socketio.emit('llm_started', {
            'question': question,
            'model': model_name,
            'session_id': session_id
        })
        
        # Query the model
        response = await model_manager.query_model(model_name, question)
        
        # Emit response
        socketio.emit('llm_response', {
            'question': question,
            'model': model_name,
            'response': response.response,
            'response_time': response.response_time,
            'error': response.error,
            'session_id': session_id
        })
        
    except Exception as e:
        socketio.emit('llm_error', {
            'message': f'Error during query processing: {str(e)}',
            'session_id': session_id
        })

def start_background_updates():
    """Start background thread for live updates."""
    def update_loop():
        while True:
            try:
                # Emit time update every second (1s)
                time_data = data_provider.get_time_data()
                socketio.emit('time_update', time_data)
                
                # Update calendar every minute (60s)
                if int(time.time()) % 60 == 0:
                    calendar_data = data_provider.get_calendar_data()
                    socketio.emit('calendar_update', calendar_data)
                
                # Update quote every 2 minutes (120s)
                if int(time.time()) % 120 == 0:
                    quote = data_provider.get_philosophy_quote()
                    socketio.emit('quote_update', quote)
                
                # Update vocabulary every 5 minutes (300s)
                if int(time.time()) % 300 == 0:
                    vocab = data_provider.get_vocabulary_word()
                    socketio.emit('vocab_update', vocab)
                
                # Update puzzle every 5 minutes (300s)
                if int(time.time()) % 300 == 0:
                    puzzle = data_provider.get_daily_puzzle()
                    socketio.emit('puzzle_update', puzzle)
                
                # Update weather every 3 minutes (180s)
                if int(time.time()) % 180 == 0:
                    weather = data_provider.get_weather_data()
                    socketio.emit('weather_update', weather)
                
                # Update system stats every 5 seconds (5s)
                if int(time.time()) % 5 == 0:
                    stats = data_provider.get_system_stats()
                    socketio.emit('system_update', stats)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Background update error: {e}")
                time.sleep(5)
    
    update_thread = threading.Thread(target=update_loop)
    update_thread.daemon = True
    update_thread.start()

if __name__ == '__main__':
    print("🚀 Starting Live Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5001")
    
    # Start background updates
    start_background_updates()
    
    print("\n🌐 Starting dashboard server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
