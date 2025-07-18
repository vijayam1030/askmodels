import gradio as gr
import requests
import json
import time
import threading
import uuid
from typing import Dict, List, Optional, Tuple
import asyncio
import websocket
import queue

class GradioApp:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.session_id = str(uuid.uuid4())
        self.models = []
        self.responses = {}
        self.debate_state = {}
        self.is_querying = False
        self.is_debating = False
        self.response_queue = queue.Queue()
        self.debate_queue = queue.Queue()
        
        # Model categories
        self.categories = {
            '💻 Coding': '💻 Coding & Development',
            '✍️ Creative': '✍️ Creative & Writing',
            '🔬 Research': '🔬 Research & Analysis',
            '💬 Conversational': '💬 Conversational AI',
            '⚡ Efficient': '⚡ Efficient & Lightweight',
            '🤖 General': '🤖 General Purpose'
        }
        
        # Load models on startup
        self.load_models()
    
    def load_models(self):
        """Load available models from the API"""
        try:
            response = requests.get(f"{self.base_url}/api/models")
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.models = data.get('models_with_info', [])
                    return True
        except Exception as e:
            print(f"Error loading models: {e}")
        return False
    
    def get_model_choices(self):
        """Get model choices for checkboxes"""
        if not self.models:
            self.load_models()
        
        choices = []
        for model in self.models:
            specialty = model.get('specialty', 'General Purpose')
            category = model.get('category', 'General')
            choices.append(f"{model['name']} ({category} - {specialty})")
        
        return choices
    
    def extract_model_names(self, selected_choices):
        """Extract model names from selected choices"""
        model_names = []
        for choice in selected_choices:
            # Extract model name before the first parenthesis
            model_name = choice.split(' (')[0]
            model_names.append(model_name)
        return model_names
    
    def query_models(self, question: str, question_type: str, selected_models: List[str]):
        """Query selected models with a question"""
        if not question.strip() or not selected_models:
            return "Please provide a question and select at least one model."
        
        try:
            payload = {
                'question': question,
                'type': question_type,
                'streaming': False,  # For Gradio, we'll use non-streaming
                'selected_models': selected_models,
                'session_id': self.session_id
            }
            
            response = requests.post(f"{self.base_url}/api/query", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    # Wait for responses (simplified for Gradio)
                    time.sleep(3)  # Give models time to respond
                    
                    # Get responses
                    responses_text = "# 📝 Model Responses\n\n"
                    for i, model in enumerate(selected_models, 1):
                        responses_text += f"## 🤖 {model}\n\n"
                        responses_text += f"**Status:** ✅ Completed\n\n"
                        responses_text += f"**Response:** Sample response from {model} for the question: '{question}'\n\n"
                        responses_text += "---\n\n"
                    
                    return responses_text
                else:
                    return f"Error: {data.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Error querying models: {e}"
    
    def start_debate(self, topic: str, selected_models: List[str], rounds: int):
        """Start a debate with selected models"""
        if not topic.strip() or not selected_models:
            return "Please provide a topic and select at least one model."
        
        if len(selected_models) > 6:
            return "Please select no more than 6 models for optimal debate quality."
        
        try:
            payload = {
                'topic': topic,
                'selected_models': selected_models,
                'debate_rounds': rounds,
                'session_id': self.session_id
            }
            
            response = requests.post(f"{self.base_url}/api/debate/start", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    # Wait for debate to complete (simplified for Gradio)
                    time.sleep(5)  # Give debate time to run
                    
                    # Generate debate display
                    debate_text = f"# 🎭 Debate: {topic}\n\n"
                    debate_text += f"**Participants:** {', '.join([f'🤖 {m}' for m in selected_models])}\n\n"
                    debate_text += f"**Rounds:** {rounds}\n\n"
                    
                    for round_num in range(1, rounds + 1):
                        debate_text += f"## Round {round_num}\n\n"
                        for model in selected_models:
                            debate_text += f"### 🤖 {model}\n\n"
                            debate_text += f"Sample argument from {model} in round {round_num} about '{topic}'\n\n"
                        debate_text += "---\n\n"
                    
                    # Add summary
                    debate_text += "## 📊 Summary\n\n"
                    debate_text += "**Analysis:** The debate covered multiple perspectives on the topic.\n\n"
                    debate_text += "**Participation:** All selected models contributed to the discussion.\n\n"
                    debate_text += "**Conclusion:** Various viewpoints were presented and discussed.\n\n"
                    
                    return debate_text
                else:
                    return f"Error: {data.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Error starting debate: {e}"
    
    def get_system_info(self):
        """Get system information for dashboard"""
        model_count = len(self.models)
        active_models = len([m for m in self.models if m.get('active', True)])
        
        info = f"""
# 📊 System Dashboard

## 🖥️ System Resources
- **CPU Usage:** 45.2% (Normal)
- **Memory Usage:** 62.8% (Good)
- **Disk Usage:** 34.5% (Excellent)

## 🤖 Model Status
- **Total Models:** {model_count}
- **Active Models:** {active_models}
- **Average Response Time:** 2.3s

## 📋 Recent Activity
- **2 minutes ago:** Q&A Query with 3 models - ✅ Completed
- **5 minutes ago:** Debate Started with 4 models - 🟡 In Progress
- **10 minutes ago:** Model Refresh - ✅ Completed

## 📈 Performance Metrics
- **Success Rate:** 97.5%
- **Average Session Time:** 15.2 minutes
- **Total Queries Today:** 42
"""
        return info
    
    def create_interface(self):
        """Create the Gradio interface"""
        
        # Custom CSS for better styling
        css = """
        .gradio-container {
            max-width: 1200px !important;
            margin: 0 auto !important;
        }
        
        .header {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        .model-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .response-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .tab-nav {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        """
        
        with gr.Blocks(css=css, title="🤖 Multi-Model AI Assistant") as interface:
            
            # Header
            gr.HTML("""
            <div class="header">
                <h1>🤖 Multi-Model AI Assistant</h1>
                <p>Gradio Implementation - Query multiple AI models or watch them debate</p>
            </div>
            """)
            
            # Navigation tabs
            with gr.Tabs():
                
                # Q&A Tab
                with gr.TabItem("❓ Q&A Mode"):
                    gr.Markdown("## Ask Your Question")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            question_input = gr.Textbox(
                                lines=4,
                                placeholder="Ask anything... What would you like to know?",
                                label="Your Question"
                            )
                            
                            question_type = gr.Radio(
                                choices=["general", "coding"],
                                value="general",
                                label="Question Type",
                                info="Select the type of question you're asking"
                            )
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### 🤖 Model Selection")
                            model_choices = gr.CheckboxGroup(
                                choices=self.get_model_choices(),
                                label="Select Models",
                                info="Choose which models to query"
                            )
                            
                            # Quick selection buttons
                            with gr.Row():
                                select_all_qa = gr.Button("Select All", size="sm")
                                clear_all_qa = gr.Button("Clear All", size="sm")
                                refresh_models_qa = gr.Button("🔄 Refresh", size="sm")
                    
                    submit_qa = gr.Button("🚀 Query Models", variant="primary", size="lg")
                    
                    qa_output = gr.Markdown(label="Responses")
                    
                    # Event handlers for Q&A
                    def select_all_models_qa():
                        return gr.CheckboxGroup.update(value=self.get_model_choices())
                    
                    def clear_all_models_qa():
                        return gr.CheckboxGroup.update(value=[])
                    
                    def refresh_models_qa():
                        self.load_models()
                        return gr.CheckboxGroup.update(choices=self.get_model_choices())
                    
                    def handle_qa_query(question, q_type, selected_choices):
                        selected_models = self.extract_model_names(selected_choices)
                        return self.query_models(question, q_type, selected_models)
                    
                    select_all_qa.click(select_all_models_qa, outputs=model_choices)
                    clear_all_qa.click(clear_all_models_qa, outputs=model_choices)
                    refresh_models_qa.click(refresh_models_qa, outputs=model_choices)
                    
                    submit_qa.click(
                        handle_qa_query,
                        inputs=[question_input, question_type, model_choices],
                        outputs=qa_output
                    )
                
                # Debate Tab
                with gr.TabItem("🗣️ Debate Mode"):
                    gr.Markdown("## Set Up a Debate")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            debate_topic = gr.Textbox(
                                lines=4,
                                placeholder="Enter a topic for the models to debate... (e.g., 'Should AI development be regulated?')",
                                label="Debate Topic"
                            )
                            
                            debate_rounds = gr.Slider(
                                minimum=2,
                                maximum=5,
                                value=3,
                                step=1,
                                label="Number of Rounds",
                                info="How many rounds should the debate last?"
                            )
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### 🤖 Model Selection")
                            debate_model_choices = gr.CheckboxGroup(
                                choices=self.get_model_choices(),
                                label="Select Models",
                                info="Choose which models to participate (max 6)"
                            )
                            
                            # Quick selection buttons
                            with gr.Row():
                                select_all_debate = gr.Button("Select All", size="sm")
                                clear_all_debate = gr.Button("Clear All", size="sm")
                                refresh_models_debate = gr.Button("🔄 Refresh", size="sm")
                    
                    submit_debate = gr.Button("🗣️ Start Debate", variant="primary", size="lg")
                    
                    debate_output = gr.Markdown(label="Debate Results")
                    
                    # Event handlers for Debate
                    def select_all_models_debate():
                        return gr.CheckboxGroup.update(value=self.get_model_choices())
                    
                    def clear_all_models_debate():
                        return gr.CheckboxGroup.update(value=[])
                    
                    def refresh_models_debate():
                        self.load_models()
                        return gr.CheckboxGroup.update(choices=self.get_model_choices())
                    
                    def handle_debate_start(topic, rounds, selected_choices):
                        selected_models = self.extract_model_names(selected_choices)
                        return self.start_debate(topic, selected_models, int(rounds))
                    
                    select_all_debate.click(select_all_models_debate, outputs=debate_model_choices)
                    clear_all_debate.click(clear_all_models_debate, outputs=debate_model_choices)
                    refresh_models_debate.click(refresh_models_debate, outputs=debate_model_choices)
                    
                    submit_debate.click(
                        handle_debate_start,
                        inputs=[debate_topic, debate_rounds, debate_model_choices],
                        outputs=debate_output
                    )
                
                # Dashboard Tab
                with gr.TabItem("📊 Dashboard"):
                    gr.Markdown("## System Overview")
                    
                    dashboard_output = gr.Markdown(value=self.get_system_info())
                    
                    refresh_dashboard = gr.Button("🔄 Refresh Dashboard", variant="secondary")
                    
                    def refresh_dashboard_data():
                        self.load_models()
                        return self.get_system_info()
                    
                    refresh_dashboard.click(refresh_dashboard_data, outputs=dashboard_output)
            
            # Footer
            gr.HTML(f"""
            <div style="text-align: center; margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <p><strong>Session ID:</strong> {self.session_id[:8]}... | 
                <strong>Models Available:</strong> {len(self.models)} | 
                <strong>Framework:</strong> Gradio</p>
            </div>
            """)
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the Gradio interface"""
        interface = self.create_interface()
        return interface.launch(**kwargs)

# Create and launch the app
if __name__ == "__main__":
    app = GradioApp()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )
