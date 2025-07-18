import streamlit as st
import requests
import json
import time
import threading
from typing import Dict, List, Optional
import asyncio
import websocket
import uuid

# Configure page
st.set_page_config(
    page_title="🤖 Multi-Model AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .model-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .model-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    .model-card.selected {
        background: #e3f2fd;
        border-color: #2196f3;
    }
    
    .response-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .status-processing {
        color: #ff9800;
        font-weight: bold;
    }
    
    .status-completed {
        color: #4caf50;
        font-weight: bold;
    }
    
    .status-error {
        color: #f44336;
        font-weight: bold;
    }
    
    .debate-round {
        background: #f8f9fa;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .participant-tag {
        background: #e9ecef;
        color: #495057;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        margin: 0.2rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitApp:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.session_id = str(uuid.uuid4())
        
        # Initialize session state
        if 'models' not in st.session_state:
            st.session_state.models = []
        if 'selected_models' not in st.session_state:
            st.session_state.selected_models = []
        if 'responses' not in st.session_state:
            st.session_state.responses = {}
        if 'debate_state' not in st.session_state:
            st.session_state.debate_state = {}
        if 'is_querying' not in st.session_state:
            st.session_state.is_querying = False
        if 'is_debating' not in st.session_state:
            st.session_state.is_debating = False
    
    def load_models(self):
        """Load available models from the API"""
        try:
            response = requests.get(f"{self.base_url}/api/models")
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    st.session_state.models = data.get('models_with_info', [])
                    return True
        except Exception as e:
            st.error(f"Error loading models: {e}")
        return False
    
    def query_models(self, question: str, question_type: str, selected_models: List[str], streaming: bool = True):
        """Query selected models with a question"""
        try:
            payload = {
                'question': question,
                'type': question_type,
                'streaming': streaming,
                'selected_models': selected_models,
                'session_id': self.session_id
            }
            
            response = requests.post(f"{self.base_url}/api/query", json=payload)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            st.error(f"Error querying models: {e}")
        return None
    
    def start_debate(self, topic: str, selected_models: List[str], rounds: int = 3):
        """Start a debate with selected models"""
        try:
            payload = {
                'topic': topic,
                'selected_models': selected_models,
                'debate_rounds': rounds,
                'session_id': self.session_id
            }
            
            response = requests.post(f"{self.base_url}/api/debate/start", json=payload)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            st.error(f"Error starting debate: {e}")
        return None
    
    def render_main_header(self):
        """Render the main header"""
        st.markdown("""
        <div class="main-header">
            <h1>🤖 Multi-Model AI Assistant</h1>
            <p>Streamlit Implementation - Query multiple AI models or watch them debate</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_model_selection(self, mode: str = "qa"):
        """Render model selection interface"""
        st.subheader("🤖 Model Selection")
        
        if not st.session_state.models:
            if st.button("Load Models"):
                self.load_models()
                st.rerun()
        
        if st.session_state.models:
            # Group models by category
            categories = {}
            for model in st.session_state.models:
                category = model.get('category', 'General')
                if category not in categories:
                    categories[category] = []
                categories[category].append(model)
            
            # Model selection
            selected_models = []
            
            for category, models in categories.items():
                with st.expander(f"{category} ({len(models)} models)", expanded=True):
                    for model in models:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if st.checkbox(
                                f"**{model['name']}** - {model.get('specialty', 'General Purpose')}",
                                key=f"{mode}_{model['name']}"
                            ):
                                selected_models.append(model['name'])
                        with col2:
                            st.caption(f"📊 {model.get('description', 'No description')}")
            
            # Quick selection buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Select All", key=f"{mode}_select_all"):
                    for model in st.session_state.models:
                        st.session_state[f"{mode}_{model['name']}"] = True
                    st.rerun()
            
            with col2:
                if st.button("Clear All", key=f"{mode}_clear_all"):
                    for model in st.session_state.models:
                        st.session_state[f"{mode}_{model['name']}"] = False
                    st.rerun()
            
            with col3:
                if st.button("Select Diverse", key=f"{mode}_diverse"):
                    # Select diverse models (one from each category)
                    for model in st.session_state.models:
                        st.session_state[f"{mode}_{model['name']}"] = False
                    
                    selected_categories = set()
                    for model in st.session_state.models:
                        category = model.get('category', 'General')
                        if category not in selected_categories and len(selected_categories) < 3:
                            st.session_state[f"{mode}_{model['name']}"] = True
                            selected_categories.add(category)
                    st.rerun()
            
            return selected_models
        
        return []
    
    def render_qa_interface(self):
        """Render Q&A interface"""
        st.header("❓ Q&A Mode")
        
        # Question input
        question = st.text_area(
            "Your Question:",
            placeholder="Ask anything... What would you like to know?",
            height=100
        )
        
        # Question type
        question_type = st.radio(
            "Question Type:",
            ["general", "coding"],
            format_func=lambda x: "💭 General" if x == "general" else "💻 Coding"
        )
        
        # Model selection
        selected_models = self.render_model_selection("qa")
        
        # Streaming toggle
        streaming = st.checkbox("Real-time responses", value=True)
        
        # Submit button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🚀 Query Models", disabled=st.session_state.is_querying or not question or not selected_models):
                st.session_state.is_querying = True
                st.session_state.responses = {}
                
                # Start query
                result = self.query_models(question, question_type, selected_models, streaming)
                if result:
                    st.success("Query started! Responses will appear below.")
                    # Note: In a real implementation, you'd use WebSocket for real-time updates
                    time.sleep(2)  # Simulate processing time
                    st.session_state.is_querying = False
                    st.rerun()
        
        with col2:
            if st.session_state.is_querying:
                st.info("⏳ Processing your query...")
        
        # Display responses
        if st.session_state.responses:
            st.subheader("📝 Responses")
            for model_name, response_data in st.session_state.responses.items():
                with st.expander(f"🤖 {model_name}", expanded=True):
                    if response_data.get('status') == 'completed':
                        st.success(f"✅ Completed in {response_data.get('time', 0):.2f}s")
                        st.markdown(response_data.get('content', ''))
                    elif response_data.get('status') == 'error':
                        st.error(f"❌ Error: {response_data.get('error', 'Unknown error')}")
                    else:
                        st.info("⏳ Processing...")
    
    def render_debate_interface(self):
        """Render debate interface"""
        st.header("🗣️ Debate Mode")
        
        # Debate topic
        topic = st.text_area(
            "Debate Topic:",
            placeholder="Enter a topic for the models to debate... (e.g., 'Should AI development be regulated?')",
            height=100
        )
        
        # Number of rounds
        rounds = st.select_slider(
            "Number of Rounds:",
            options=[2, 3, 4, 5],
            value=3,
            format_func=lambda x: f"{x} Rounds - {'Quick' if x == 2 else 'Standard' if x == 3 else 'Extended' if x == 4 else 'Comprehensive'}"
        )
        
        # Model selection
        selected_models = self.render_model_selection("debate")
        
        # Debate controls
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗣️ Start Debate", disabled=st.session_state.is_debating or not topic or not selected_models):
                if len(selected_models) > 6:
                    st.error("Please select no more than 6 models for optimal debate quality")
                else:
                    st.session_state.is_debating = True
                    st.session_state.debate_state = {}
                    
                    # Start debate
                    result = self.start_debate(topic, selected_models, rounds)
                    if result:
                        st.success("Debate started! Watch the discussion unfold below.")
                        # Note: In a real implementation, you'd use WebSocket for real-time updates
                        time.sleep(2)
                        st.session_state.is_debating = False
                        st.rerun()
        
        with col2:
            if st.session_state.is_debating:
                st.info("⏳ Debate in progress...")
        
        # Display debate
        if st.session_state.debate_state:
            st.subheader("🎭 Live Debate")
            
            # Participants
            participants = st.session_state.debate_state.get('participants', selected_models)
            st.write("**Participants:**")
            participant_tags = " ".join([f'<span class="participant-tag">🤖 {p}</span>' for p in participants])
            st.markdown(participant_tags, unsafe_allow_html=True)
            
            # Progress
            current_round = st.session_state.debate_state.get('current_round', 1)
            total_rounds = st.session_state.debate_state.get('total_rounds', rounds)
            progress = (current_round - 1) / total_rounds
            st.progress(progress, text=f"Round {current_round} of {total_rounds}")
            
            # Debate rounds
            for round_num in range(1, current_round + 1):
                st.subheader(f"Round {round_num}")
                round_data = st.session_state.debate_state.get(f'round_{round_num}', {})
                
                for model_name, response in round_data.items():
                    with st.expander(f"🤖 {model_name}", expanded=True):
                        st.markdown(response.get('content', ''))
                        if response.get('time'):
                            st.caption(f"⏱️ {response['time']:.2f}s")
    
    def render_dashboard(self):
        """Render dashboard interface"""
        st.header("📊 Dashboard")
        
        # System info
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🖥️ System Resources")
            
            # Mock system data
            cpu_usage = 45.2
            memory_usage = 62.8
            disk_usage = 34.5
            
            st.metric("CPU Usage", f"{cpu_usage}%", delta=f"{cpu_usage-40:.1f}%")
            st.metric("Memory Usage", f"{memory_usage}%", delta=f"{memory_usage-60:.1f}%")
            st.metric("Disk Usage", f"{disk_usage}%", delta=f"{disk_usage-30:.1f}%")
        
        with col2:
            st.subheader("🤖 Model Status")
            
            # Mock model data
            total_models = len(st.session_state.models) if st.session_state.models else 0
            active_models = len([m for m in st.session_state.models if m.get('active', True)]) if st.session_state.models else 0
            
            st.metric("Total Models", total_models)
            st.metric("Active Models", active_models)
            st.metric("Avg Response Time", "2.3s", delta="-0.2s")
        
        # Activity log
        st.subheader("📋 Recent Activity")
        activity_data = [
            {"time": "2 minutes ago", "action": "Q&A Query", "models": 3, "status": "Completed"},
            {"time": "5 minutes ago", "action": "Debate Started", "models": 4, "status": "In Progress"},
            {"time": "10 minutes ago", "action": "Model Refresh", "models": 8, "status": "Completed"},
        ]
        
        for activity in activity_data:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    st.text(activity["time"])
                with col2:
                    st.text(activity["action"])
                with col3:
                    st.text(f"{activity['models']} models")
                with col4:
                    status_color = "🟢" if activity["status"] == "Completed" else "🟡"
                    st.text(f"{status_color} {activity['status']}")
    
    def run(self):
        """Main app runner"""
        self.render_main_header()
        
        # Load models on startup
        if not st.session_state.models:
            self.load_models()
        
        # Sidebar navigation
        with st.sidebar:
            st.title("Navigation")
            mode = st.radio(
                "Select Mode:",
                ["Q&A", "Debate", "Dashboard"],
                format_func=lambda x: f"❓ {x}" if x == "Q&A" else f"🗣️ {x}" if x == "Debate" else f"📊 {x}"
            )
            
            st.divider()
            
            # Settings
            st.subheader("⚙️ Settings")
            if st.button("🔄 Refresh Models"):
                self.load_models()
                st.rerun()
            
            # Stats
            st.subheader("📊 Stats")
            st.metric("Available Models", len(st.session_state.models))
            st.metric("Session ID", self.session_id[:8] + "...")
        
        # Main content
        if mode == "Q&A":
            self.render_qa_interface()
        elif mode == "Debate":
            self.render_debate_interface()
        elif mode == "Dashboard":
            self.render_dashboard()

# Run the app
if __name__ == "__main__":
    app = StreamlitApp()
    app.run()
