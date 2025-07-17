#!/usr/bin/env python3
"""
Multi-Model Query Application
Queries multiple models through Ollama for both general and coding questions.
"""

import asyncio
from typing import Optional, Tuple

from models import (
    OllamaModelManager, 
    ConfigManager, 
    QuestionType, 
    PromptEnhancer
)
from ui import UserInterface, ProgressIndicator


class MultiModelApp:
    """Main application class for multi-model querying."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.model_manager = OllamaModelManager(self.config_manager)
        self.ui = UserInterface()
        self.available_models = []
    
    def initialize(self) -> bool:
        """Initialize the application by fetching available models."""
        progress = ProgressIndicator("🔍 Checking available models from Ollama")
        progress.start()
        
        self.available_models = self.model_manager.get_available_models()
        progress.stop()
        
        if not self.available_models:
            self.ui.display_error("No models found. Please ensure Ollama is running and has models installed.")
            self.ui.display_info("Try running: ollama list")
            return False
        
        coding_models = self.model_manager.get_models_for_question_type(QuestionType.CODING)
        self.ui.display_models_status(len(self.available_models), len(coding_models))
        
        return True
    
    def get_user_input(self) -> Tuple[Optional[str], Optional[QuestionType], bool]:
        """Get user input and determine question type and streaming preference."""
        choice = self.ui.get_menu_choice()
        
        if choice == "1":  # General question with streaming
            question = self.ui.get_question(QuestionType.GENERAL)
            if question:
                return question, QuestionType.GENERAL, True
        elif choice == "2":  # Coding question with streaming
            question = self.ui.get_question(QuestionType.CODING)
            if question:
                return question, QuestionType.CODING, True
        elif choice == "3":  # General question without streaming
            question = self.ui.get_question(QuestionType.GENERAL)
            if question:
                return question, QuestionType.GENERAL, False
        elif choice == "4":  # Coding question without streaming
            question = self.ui.get_question(QuestionType.CODING)
            if question:
                return question, QuestionType.CODING, False
        elif choice == "5":
            self.show_available_models()
        elif choice == "6":
            self.ui.display_info("Refreshing models...")
            self.initialize()
        elif choice == "7":
            self.show_configuration()
        elif choice == "8":
            return "exit", None, False
        else:
            self.ui.display_error("Invalid choice. Please try again.")
        
        return None, None, False
    
    def show_available_models(self):
        """Display available models with their categories."""
        coding_models = self.model_manager.get_models_for_question_type(QuestionType.CODING)
        self.ui.display_available_models(self.available_models, coding_models)
    
    def show_configuration(self):
        """Display current configuration."""
        self.ui.display_config(self.config_manager.config)
    
    async def process_question(self, question: str, question_type: QuestionType):
        """Process a question by querying appropriate models with streaming."""
        models_to_query = self.model_manager.get_models_for_question_type(question_type)
        
        if not models_to_query:
            self.ui.display_error("No suitable models found for this question type.")
            return
        
        # Enhance the prompt based on question type
        enhanced_prompt = PromptEnhancer.enhance_prompt(question, question_type)
        
        # Display streaming start information
        self.ui.display_streaming_start(question, models_to_query, question_type)
        
        # Get streaming callback
        streaming_callback = self.ui.get_streaming_callback()
        
        # Query models with streaming (3 at a time)
        try:
            responses = await self.model_manager.query_multiple_models(
                models_to_query, 
                enhanced_prompt, 
                max_concurrent=3, 
                stream=True, 
                callback=streaming_callback
            )
            
            # Display summary after all streaming is complete
            self.ui.streaming_display.display_summary(responses)
            
        except Exception as e:
            self.ui.display_error(f"An error occurred while querying models: {e}")

    async def process_question_non_streaming(self, question: str, question_type: QuestionType):
        """Process a question without streaming (original behavior)."""
        models_to_query = self.model_manager.get_models_for_question_type(question_type)
        
        if not models_to_query:
            self.ui.display_error("No suitable models found for this question type.")
            return
        
        # Enhance the prompt based on question type
        enhanced_prompt = PromptEnhancer.enhance_prompt(question, question_type)
        
        # Display query information
        self.ui.display_query_start(question, models_to_query, question_type)
        
        # Query models without streaming
        try:
            responses = await self.model_manager.query_multiple_models(
                models_to_query, 
                enhanced_prompt, 
                max_concurrent=3, 
                stream=False
            )
            self.ui.display_responses(responses, question_type)
        except Exception as e:
            self.ui.display_error(f"An error occurred while querying models: {e}")
    
    async def run(self):
        """Main application loop."""
        self.ui.display_banner()
        
        if not self.initialize():
            return
        
        while True:
            try:
                self.ui.display_menu()
                question, question_type, use_streaming = self.get_user_input()
                
                if question == "exit":
                    break
                elif question and question_type is not None:
                    if use_streaming:
                        await self.process_question(question, question_type)
                    else:
                        await self.process_question_non_streaming(question, question_type)
                
                if question:  # Only wait if we processed something
                    self.ui.wait_for_enter()
                
            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                self.ui.display_error(f"An unexpected error occurred: {e}")
                self.ui.wait_for_enter()
        
        self.ui.display_goodbye()


def main():
    """Entry point of the application."""
    app = MultiModelApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n👋 Application terminated by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    main()
