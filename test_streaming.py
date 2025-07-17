#!/usr/bin/env python3
"""
Test script for streaming functionality
"""

import asyncio
from models import ConfigManager, OllamaModelManager, QuestionType, PromptEnhancer

async def test_streaming():
    """Test the streaming functionality."""
    print("🧪 Testing Streaming Functionality")
    print("=" * 40)
    
    # Initialize components
    config_manager = ConfigManager()
    model_manager = OllamaModelManager(config_manager)
    
    # Get available models
    models = model_manager.get_available_models()
    if not models:
        print("❌ No models available. Please ensure Ollama is running.")
        return
    
    print(f"✅ Found {len(models)} models: {', '.join(models[:3])}...")
    
    # Test streaming callback
    async def test_callback(model_name: str, chunk: str, is_done: bool):
        if chunk and not is_done:
            print(f"[{model_name}] {chunk}", end="", flush=True)
        elif is_done:
            print(f"\n✅ {model_name} completed")
    
    # Test with a simple question
    test_question = "What is 2+2?"
    enhanced_prompt = PromptEnhancer.enhance_prompt(test_question, QuestionType.GENERAL)
    
    print(f"\n🔍 Testing with question: {test_question}")
    print("🔄 Streaming responses...\n")
    
    # Use only first 2 models for testing
    test_models = models[:2]
    
    try:
        responses = await model_manager.query_multiple_models(
            test_models,
            enhanced_prompt,
            max_concurrent=2,
            stream=True,
            callback=test_callback
        )
        
        print(f"\n📊 Test completed!")
        print(f"✅ {len([r for r in responses if r.is_successful()])} successful")
        print(f"❌ {len([r for r in responses if not r.is_successful()])} failed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_streaming())
