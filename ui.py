"""
User interface module for the multi-model query application.
"""

import time
from typing import List, Optional, Tuple
from models import ModelResponse, QuestionType


class StreamingDisplay:
    """Handles streaming display of model responses."""
    
    def __init__(self):
        self.model_outputs = {}
        self.model_start_times = {}
        self.completed_models = set()
    
    def start_model(self, model_name: str):
        """Start tracking a model's output."""
        self.model_outputs[model_name] = ""
        self.model_start_times[model_name] = time.time()
        print(f"\n🤖 {model_name}: Starting...")
    
    def add_chunk(self, model_name: str, chunk: str):
        """Add a chunk of text to a model's output."""
        if model_name not in self.model_outputs:
            self.model_outputs[model_name] = ""
        
        self.model_outputs[model_name] += chunk
        # Print the chunk in real-time
        print(chunk, end="", flush=True)
    
    def complete_model(self, model_name: str):
        """Mark a model as completed."""
        if model_name not in self.completed_models:
            self.completed_models.add(model_name)
            elapsed = time.time() - self.model_start_times.get(model_name, 0)
            print(f"\n✅ {model_name} completed in {elapsed:.2f}s")
            print("-" * 40)
    
    def display_summary(self, responses: List[ModelResponse]):
        """Display a summary after all streaming is complete."""
        successful = [r for r in responses if r.is_successful()]
        failed = [r for r in responses if not r.is_successful()]
        
        print("\n📊 STREAMING SUMMARY")
        print("=" * 50)
        print(f"✅ {len(successful)} successful • ❌ {len(failed)} failed")
        
        if failed:
            print("\n❌ FAILED MODELS:")
            for response in failed:
                print(f"   • {response.model_name}: {response.error}")


class UserInterface:
    """Handles user interaction and display formatting."""
    
    def __init__(self):
        self.streaming_display = StreamingDisplay()
    
    @staticmethod
    def display_banner():
        """Display application banner."""
        print("\n" + "="*60)
        print("🤖 MULTI-MODEL QUERY APPLICATION")
        print("="*60)
    
    @staticmethod
    def display_menu():
        """Display the main menu."""
        print("\n📋 MAIN MENU")
        print("-" * 30)
        print("1. 📝 Ask General Question (Streaming)")
        print("2. 💻 Ask Coding Question (Streaming)")
        print("3. � Ask General Question (Wait for All)")
        print("4. 🖥️  Ask Coding Question (Wait for All)")
        print("5. �📊 Show Available Models")
        print("6. 🔄 Refresh Models")
        print("7. ⚙️  Show Configuration")
        print("8. 🚪 Exit")
        print("-" * 30)
    
    @staticmethod
    def get_menu_choice() -> str:
        """Get user menu choice."""
        return input("\nSelect an option (1-8): ").strip()
    
    @staticmethod
    def get_question(question_type: QuestionType) -> str:
        """Get question from user based on type."""
        if question_type == QuestionType.CODING:
            prompt = "\n💻 Enter your coding question: "
        else:
            prompt = "\n📝 Enter your general question: "
        
        return input(prompt).strip()
    
    @staticmethod
    def display_models_status(total_models: int, coding_models: int):
        """Display model status summary."""
        print(f"\n✅ Found {total_models} total models")
        print(f"💻 {coding_models} coding-capable models identified")
    
    @staticmethod
    def display_available_models(all_models: List[str], coding_models: List[str]):
        """Display available models with their categories."""
        print(f"\n📋 AVAILABLE MODELS ({len(all_models)} total)")
        print("="*50)
        
        if coding_models:
            print(f"\n💻 CODING-CAPABLE MODELS ({len(coding_models)}):")
            for model in coding_models:
                print(f"   ✓ {model}")
        
        print("\n🌐 ALL AVAILABLE MODELS:")
        for model in all_models:
            is_coding = model in coding_models
            marker = "💻" if is_coding else "📝"
            print(f"   {marker} {model}")
    
    @staticmethod
    def display_query_start(question: str, models: List[str], question_type: QuestionType):
        """Display query start information (non-streaming)."""
        type_name = "coding" if question_type == QuestionType.CODING else "general"
        type_emoji = "💻" if question_type == QuestionType.CODING else "📝"
        
        print(f"\n{type_emoji} PROCESSING {type_name.upper()} QUESTION")
        print("="*60)
        print(f"❓ Question: {question}")
        print(f"🤖 Querying {len(models)} models: {', '.join(models)}")
        print("⏳ Please wait...")

    @staticmethod
    def display_streaming_start(question: str, models: List[str], question_type: QuestionType):
        """Display start of streaming query."""
        type_name = "coding" if question_type == QuestionType.CODING else "general"
        type_emoji = "💻" if question_type == QuestionType.CODING else "📝"
        
        print(f"\n{type_emoji} STREAMING {type_name.upper()} RESPONSES")
        print("="*60)
        print(f"❓ Question: {question}")
        print(f"🤖 Querying {len(models)} models: {', '.join(models)}")
        print("🔄 Processing in batches of 3...")
        print("⚡ Streaming responses as they arrive...\n")

    def get_streaming_callback(self):
        """Get a callback function for streaming responses."""
        async def streaming_callback(model_name: str, chunk: str, is_done: bool):
            if chunk and not is_done:
                # If this is the first chunk from this model, start tracking
                if model_name not in self.streaming_display.model_outputs:
                    self.streaming_display.start_model(model_name)
                
                self.streaming_display.add_chunk(model_name, chunk)
            elif is_done:
                self.streaming_display.complete_model(model_name)
        
        return streaming_callback
    
    @staticmethod
    def display_responses(responses: List[ModelResponse], question_type: QuestionType):
        """Display responses from all models."""
        successful_responses = [r for r in responses if r.is_successful()]
        failed_responses = [r for r in responses if not r.is_successful()]
        
        type_emoji = "💻" if question_type == QuestionType.CODING else "📝"
        
        print(f"\n{type_emoji} RESULTS")
        print("="*80)
        print(f"✅ {len(successful_responses)} successful • ❌ {len(failed_responses)} failed")
        
        # Display successful responses
        if successful_responses:
            print("\n📊 SUCCESSFUL RESPONSES:")
            
            # Sort by response time for better UX
            successful_responses.sort(key=lambda x: x.response_time)
            
            for i, response in enumerate(successful_responses, 1):
                print(f"\n{'-'*80}")
                print(f"🤖 MODEL: {response.model_name}")
                print(f"⏱️  RESPONSE TIME: {response.response_time:.2f}s")
                print("💬 RESPONSE:")
                print("-" * 40)
                print(response.response.strip())
                if i < len(successful_responses):
                    print("-" * 40)
        
        # Display failed responses
        if failed_responses:
            print("\n❌ FAILED RESPONSES:")
            for response in failed_responses:
                print(f"   • {response.model_name}: {response.error}")
    
    @staticmethod
    def display_config(config_dict: dict):
        """Display current configuration."""
        print("\n⚙️  CURRENT CONFIGURATION")
        print("="*40)
        print(f"🌐 Ollama URL: {config_dict.get('ollama_url', 'Not set')}")
        print(f"⏱️  Request Timeout: {config_dict.get('request_timeout', 'Not set')}s")
        print(f"🔀 Max Concurrent: {config_dict.get('max_concurrent_requests', 'Not set')}")
        
        coding_models = config_dict.get('coding_models', [])
        print(f"\n💻 Coding Models Patterns ({len(coding_models)}):")
        for model in coding_models:
            print(f"   • {model}")
    
    @staticmethod
    def display_error(message: str):
        """Display error message."""
        print(f"\n❌ Error: {message}")
    
    @staticmethod
    def display_success(message: str):
        """Display success message."""
        print(f"\n✅ {message}")
    
    @staticmethod
    def display_warning(message: str):
        """Display warning message."""
        print(f"\n⚠️  Warning: {message}")
    
    @staticmethod
    def display_info(message: str):
        """Display info message."""
        print(f"\nℹ️  {message}")
    
    @staticmethod
    def wait_for_enter():
        """Wait for user to press Enter."""
        input("\nPress Enter to continue...")
    
    @staticmethod
    def display_goodbye():
        """Display goodbye message."""
        print("\n👋 Thank you for using Multi-Model Query Application!")
        print("🚀 Happy coding and questioning!")


class ProgressIndicator:
    """Simple progress indicator for long-running operations."""
    
    def __init__(self, message: str = "Processing"):
        self.message = message
        self.active = False
    
    def start(self):
        """Start the progress indicator."""
        self.active = True
        print(f"{self.message}...", end="", flush=True)
    
    def update(self, step: str = "."):
        """Update progress indicator."""
        if self.active:
            print(step, end="", flush=True)
    
    def stop(self, final_message: str = "Done"):
        """Stop the progress indicator."""
        if self.active:
            print(f" {final_message}")
            self.active = False
