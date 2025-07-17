#!/usr/bin/env python3
"""
Test script for system resource integration.
"""

import sys
import time
from config import ConfigManager
from models import OllamaModelManager, QuestionType

def test_system_integration():
    """Test the system resource integration."""
    print("🧪 Testing System Resource Integration")
    print("=" * 50)
    
    try:
        # Initialize components
        config_manager = ConfigManager()
        model_manager = OllamaModelManager(config_manager)
        
        print("✅ Components initialized successfully")
        
        # Test system resource detection
        print("\n🔍 System Resource Detection:")
        info = model_manager.resource_manager.system_info
        print(f"   💾 RAM: {info.available_ram_gb:.1f}GB available / {info.total_ram_gb:.1f}GB total")
        print(f"   🔧 CPU: {info.cpu_cores} cores")
        
        if info.gpus:
            print(f"   🎮 GPU: {len(info.gpus)} detected")
            for i, gpu in enumerate(info.gpus):
                print(f"      {i+1}. {gpu['name']} ({gpu['memory_gb']:.1f}GB)")
        else:
            print("   🎮 GPU: None detected (CPU only)")
        
        # Test model list refresh
        print("\n🔄 Testing Model List Refresh:")
        models = model_manager.get_available_models(force_refresh=True)
        print(f"   📋 Found {len(models)} models")
        
        if models:
            # Test system optimization
            print("\n⚡ Testing System Optimization:")
            optimal_concurrent, prioritized = model_manager.resource_manager.optimize_concurrent_models(models)
            print(f"   🎯 Optimal concurrency: {optimal_concurrent}")
            print(f"   📊 Prioritized models: {len(prioritized)}")
            
            # Test model analysis
            print("\n🔬 Model Analysis:")
            model_manager.print_model_analysis(models[:5])  # Analyze first 5 models
            
            # Test question type filtering
            print("\n🏷️  Testing Question Type Filtering:")
            coding_models = model_manager.get_models_for_question_type(QuestionType.CODING)
            general_models = model_manager.get_models_for_question_type(QuestionType.GENERAL)
            
            print(f"   💻 Coding models: {len(coding_models)}")
            print(f"   📝 General models: {len(general_models)}")
            
            # Test optimal concurrency calculation
            print("\n⚙️  Testing Concurrency Optimization:")
            optimal_coding = model_manager.get_optimal_concurrency(coding_models)
            optimal_general = model_manager.get_optimal_concurrency(general_models)
            
            print(f"   💻 Optimal coding concurrency: {optimal_coding}")
            print(f"   📝 Optimal general concurrency: {optimal_general}")
        else:
            print("   ⚠️  No models available for testing")
        
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_system_integration()
    
    if success:
        print("\n🎉 System integration is working correctly!")
        print("\n💡 You can now:")
        print("   • Run the console app: python main.py")
        print("   • Run the web app: python web_app.py")
        print("   • Models will be automatically refreshed")
        print("   • System resources will optimize concurrency")
        
    else:
        print("\n💥 System integration test failed!")
        print("   Please check the error messages above.")
        
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
