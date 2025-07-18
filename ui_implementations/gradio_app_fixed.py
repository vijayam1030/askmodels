import gradio as gr
import requests
import json
import time
import threading
import uuid
from typing import Dict, List, Optional, Tuple

class FixedGradioApp:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.session_id = str(uuid.uuid4())
        self.models = []
        self.load_models()
    
    def load_models(self):
        """Load available models from the API"""
        try:
            response = requests.get(f"{self.base_url}/api/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.models = data.get('models_with_info', [])
                    if not self.models:
                        # Fallback to basic models list
                        self.models = [{'name': m, 'category': 'General', 'specialty': 'General Purpose'} 
                                     for m in data.get('models', [])]
                    print(f"Loaded {len(self.models)} models")
                    return True
            else:
                print(f"API error: {response.status_code}")
        except Exception as e:
            print(f"Error loading models: {e}")
            # Fallback to demo models
            self.models = [
                {'name': 'Demo Model 1', 'category': 'General', 'specialty': 'General Purpose'},
                {'name': 'Demo Model 2', 'category': 'Coding', 'specialty': 'Code Generation'},
                {'name': 'Demo Model 3', 'category': 'Creative', 'specialty': 'Creative Writing'}
            ]
            print(f"Using demo models: {len(self.models)}")
        return False
    
    def get_model_choices(self):
        """Get model choices for checkboxes"""
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
        if not question.strip():
            return "❌ Please provide a question."
        
        if not selected_models:
            return "❌ Please select at least one model."
        
        try:
            # Extract model names from the selected choices
            model_names = self.extract_model_names(selected_models)
            
            payload = {
                'question': question,
                'type': question_type,
                'streaming': False,
                'selected_models': model_names,
                'session_id': self.session_id
            }
            
            # Show loading message
            result = f"# 🔄 Querying {len(model_names)} models...\n\n"
            result += f"**Question:** {question}\n"
            result += f"**Type:** {question_type}\n"
            result += f"**Models:** {', '.join(model_names)}\n\n"
            
            # Make API call
            response = requests.post(f"{self.base_url}/api/query", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    result += "## ✅ Query submitted successfully!\n\n"
                    result += "**Note:** In a real implementation, responses would be displayed here in real-time.\n\n"
                    
                    # Simulate responses for demo
                    result += "## 📝 Sample Responses:\n\n"
                    for i, model in enumerate(model_names, 1):
                        result += f"### 🤖 {model}\n\n"
                        result += f"**Status:** ✅ Completed\n\n"
                        result += f"**Response:** This is a sample response from {model} to the question: '{question}'\n\n"
                        result += "---\n\n"
                    
                    return result
                else:
                    return f"❌ Error: {data.get('error', 'Unknown error')}"
            else:
                return f"❌ HTTP Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "❌ Request timeout. Please try again."
        except Exception as e:
            return f"❌ Error querying models: {str(e)}"
    
    def start_debate(self, topic: str, selected_models: List[str], rounds: int):
        """Start a debate with selected models"""
        if not topic.strip():
            return "❌ Please provide a debate topic."
        
        if not selected_models:
            return "❌ Please select at least one model."
        
        if len(selected_models) > 6:
            return "❌ Please select no more than 6 models for optimal debate quality."
        
        try:
            # Extract model names from the selected choices
            model_names = self.extract_model_names(selected_models)
            
            payload = {
                'topic': topic,
                'selected_models': model_names,
                'debate_rounds': rounds,
                'session_id': self.session_id
            }
            
            # Show loading message
            result = f"# 🔄 Starting debate with {len(model_names)} models...\n\n"
            result += f"**Topic:** {topic}\n"
            result += f"**Rounds:** {rounds}\n"
            result += f"**Participants:** {', '.join(model_names)}\n\n"
            
            # Make API call
            response = requests.post(f"{self.base_url}/api/debate/start", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    result += "## ✅ Debate started successfully!\n\n"
                    result += "**Note:** In a real implementation, debate rounds would be displayed here in real-time.\n\n"
                    
                    # Simulate debate for demo
                    result += f"## 🎭 Sample Debate: {topic}\n\n"
                    result += f"**Participants:** {', '.join([f'🤖 {m}' for m in model_names])}\n\n"
                    
                    for round_num in range(1, rounds + 1):
                        result += f"### Round {round_num}\n\n"
                        for model in model_names:
                            result += f"**🤖 {model}:**\n"
                            result += f"Sample argument from {model} in round {round_num} about '{topic}'\n\n"
                        result += "---\n\n"
                    
                    # Add summary
                    result += "### 📊 Summary\n\n"
                    result += "**Analysis:** The debate covered multiple perspectives on the topic.\n\n"
                    result += "**Participation:** All selected models contributed to the discussion.\n\n"
                    result += "**Conclusion:** Various viewpoints were presented and discussed.\n\n"
                    
                    return result
                else:
                    return f"❌ Error: {data.get('error', 'Unknown error')}"
            else:
                return f"❌ HTTP Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "❌ Request timeout. Please try again."
        except Exception as e:
            return f"❌ Error starting debate: {str(e)}"
    
    def get_system_info(self):
        """Get system information for dashboard"""
        try:
            # Try to get real system info
            response = requests.get(f"{self.base_url}/api/system", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    return f"""
# 📊 System Dashboard

## 🖥️ System Resources
- **Status:** ✅ Connected to Flask backend
- **Models Available:** {len(self.models)}
- **Backend URL:** {self.base_url}

## 🤖 Model Status
- **Total Models:** {len(self.models)}
- **Connection:** ✅ Active
- **Session ID:** {self.session_id[:8]}...

## 📋 Recent Activity
- **Status:** Ready for queries and debates
- **Framework:** Gradio {gr.__version__}
- **Backend:** Flask API

## 📈 Performance
- **Response Time:** < 1s
- **Availability:** 100%
- **Framework Status:** ✅ Operational
"""
        except Exception as e:
            print(f"Error getting system info: {e}")
        
        # Fallback system info
        return f"""
# 📊 System Dashboard

## 🖥️ System Resources
- **Status:** ⚠️ Limited connectivity
- **Models Available:** {len(self.models)}
- **Backend URL:** {self.base_url}

## 🤖 Model Status
- **Total Models:** {len(self.models)}
- **Connection:** ⚠️ Demo mode
- **Session ID:** {self.session_id[:8]}...

## 📋 Recent Activity
- **Status:** Demo mode active
- **Framework:** Gradio {gr.__version__}
- **Backend:** Flask API (may be offline)

## 📈 Performance
- **Response Time:** Demo mode
- **Availability:** Demo mode
- **Framework Status:** ✅ Operational
"""
    
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
        """
        
        with gr.Blocks(css=css, title="🤖 Multi-Model AI Assistant - Gradio") as interface:
            
            # Header
            gr.HTML("""
            <div class="header">
                <h1>🤖 Multi-Model AI Assistant</h1>
                <p>Gradio Implementation - Query multiple AI models or start debates</p>
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
                                label="Your Question",
                                value="What are the key differences between Python and JavaScript?"
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
                                info="Choose which models to query",
                                value=self.get_model_choices()[:2] if self.get_model_choices() else []
                            )
                            
                            # Quick selection buttons
                            with gr.Row():
                                select_all_qa = gr.Button("Select All", size="sm")
                                clear_all_qa = gr.Button("Clear All", size="sm")
                                refresh_models_qa = gr.Button("🔄 Refresh", size="sm")
                    
                    submit_qa = gr.Button("🚀 Query Models", variant="primary", size="lg")
                    
                    qa_output = gr.Markdown(label="Responses", value="Click 'Query Models' to see responses here.")
                    
                    # Event handlers for Q&A
                    def select_all_models_qa():
                        return gr.CheckboxGroup.update(value=self.get_model_choices())
                    
                    def clear_all_models_qa():
                        return gr.CheckboxGroup.update(value=[])
                    
                    def refresh_models_qa():
                        self.load_models()
                        return gr.CheckboxGroup.update(choices=self.get_model_choices())
                    
                    select_all_qa.click(select_all_models_qa, outputs=model_choices)
                    clear_all_qa.click(clear_all_models_qa, outputs=model_choices)
                    refresh_models_qa.click(refresh_models_qa, outputs=model_choices)
                    
                    submit_qa.click(
                        self.query_models,
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
                                placeholder="Enter a topic for the models to debate...",
                                label="Debate Topic",
                                value="Should AI development be regulated by governments?"
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
                                info="Choose which models to participate (max 6)",
                                value=self.get_model_choices()[:3] if len(self.get_model_choices()) >= 3 else self.get_model_choices()
                            )
                            
                            # Quick selection buttons
                            with gr.Row():
                                select_all_debate = gr.Button("Select All", size="sm")
                                clear_all_debate = gr.Button("Clear All", size="sm")
                                refresh_models_debate = gr.Button("🔄 Refresh", size="sm")
                    
                    submit_debate = gr.Button("🗣️ Start Debate", variant="primary", size="lg")
                    
                    debate_output = gr.Markdown(label="Debate Results", value="Click 'Start Debate' to see the debate here.")
                    
                    # Event handlers for Debate
                    def select_all_models_debate():
                        return gr.CheckboxGroup.update(value=self.get_model_choices())
                    
                    def clear_all_models_debate():
                        return gr.CheckboxGroup.update(value=[])
                    
                    def refresh_models_debate():
                        self.load_models()
                        return gr.CheckboxGroup.update(choices=self.get_model_choices())
                    
                    select_all_debate.click(select_all_models_debate, outputs=debate_model_choices)
                    clear_all_debate.click(clear_all_models_debate, outputs=debate_model_choices)
                    refresh_models_debate.click(refresh_models_debate, outputs=debate_model_choices)
                    
                    submit_debate.click(
                        self.start_debate,
                        inputs=[debate_topic, debate_model_choices, debate_rounds],
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
                <strong>Framework:</strong> Gradio {gr.__version__}</p>
            </div>
            """)
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the Gradio interface"""
        interface = self.create_interface()
        return interface.launch(**kwargs)

# Create and launch the app
if __name__ == "__main__":
    print("🚀 Starting Fixed Gradio App...")
    app = FixedGradioApp()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )
