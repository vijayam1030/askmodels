#!/usr/bin/env python3
"""
Model Diagnostic Script
Tests each model individually to identify issues
"""

import asyncio
import requests
import time
from models import ConfigManager, OllamaModelManager, QuestionType

async def test_individual_models():
    """Test each model individually to identify issues."""
    print("🔍 OLLAMA MODEL DIAGNOSTIC")
    print("=" * 50)
    
    # Initialize
    config_manager = ConfigManager()
    model_manager = OllamaModelManager(config_manager)
    
    # First, check Ollama connection
    print("📡 Testing Ollama connection...")
    try:
        response = requests.get(f"{config_manager.get('ollama_url')}/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama server is accessible")
        else:
            print(f"❌ Ollama server returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return
    
    # Get available models
    print("\n📋 Getting model list...")
    available_models = model_manager.get_available_models()
    
    if not available_models:
        print("❌ No models found")
        return
    
    print(f"✅ Found {len(available_models)} models")
    
    # Test each model with a simple prompt
    test_prompt = "Hello! Please respond with 'OK' if you can hear me."
    
    print(f"\n🧪 Testing each model with prompt: '{test_prompt}'")
    print("-" * 60)
    
    working_models = []
    failed_models = []
    
    for i, model in enumerate(available_models, 1):
        print(f"\n[{i}/{len(available_models)}] Testing {model}...")
        
        try:
            # Test with a short timeout to identify slow/problematic models
            start_time = time.time()
            
            # Try a simple non-streaming request first
            response = await model_manager.query_model(model, test_prompt, stream=False)
            
            elapsed = time.time() - start_time
            
            if response.error:
                print(f"❌ {model}: {response.error}")
                failed_models.append((model, response.error))
            else:
                response_preview = response.response[:50] + "..." if len(response.response) > 50 else response.response
                print(f"✅ {model}: OK ({elapsed:.1f}s) - '{response_preview}'")
                working_models.append(model)
                
        except Exception as e:
            print(f"❌ {model}: Exception - {e}")
            failed_models.append((model, str(e)))
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 50)
    print(f"✅ Working models: {len(working_models)}")
    print(f"❌ Failed models: {len(failed_models)}")
    
    if working_models:
        print(f"\n✅ WORKING MODELS:")
        for model in working_models:
            print(f"   • {model}")
    
    if failed_models:
        print(f"\n❌ FAILED MODELS:")
        for model, error in failed_models:
            print(f"   • {model}: {error}")
    
    # Test coding models specifically
    coding_models = model_manager.get_models_for_question_type(QuestionType.CODING)
    working_coding_models = [m for m in working_models if m in coding_models]
    
    print(f"\n💻 CODING MODELS STATUS:")
    print(f"   Total coding models: {len(coding_models)}")
    print(f"   Working coding models: {len(working_coding_models)}")
    
    if len(working_coding_models) < len(coding_models):
        failed_coding = [m for m in coding_models if m not in working_models]
        print(f"   Failed coding models: {failed_coding}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if failed_models:
        print("• Check if failed models are properly pulled:")
        for model, _ in failed_models:
            print(f"  ollama pull {model}")
        print("• Consider increasing timeout in config.json")
        print("• Check Ollama server logs for detailed errors")
    
    if len(working_models) >= 3:
        print("• You have enough working models for the application")
    else:
        print("• Consider pulling more models for better functionality")

if __name__ == "__main__":
    asyncio.run(test_individual_models())
