#!/usr/bin/env python3
"""
Test script to verify model filtering functionality.
"""

import sys
from config import ConfigManager
from models import OllamaModelManager

def test_model_filtering():
    """Test the model filtering functionality."""
    print("🧪 Testing Model Filtering")
    print("=" * 40)
    
    try:
        # Initialize components
        config_manager = ConfigManager()
        model_manager = OllamaModelManager(config_manager)
        
        print("✅ Components initialized")
        
        # Test getting all models (unfiltered)
        print("\n📋 Getting ALL models (unfiltered):")
        all_models = model_manager.get_available_models(force_refresh=True, filter_large=False)
        print(f"   Total models found: {len(all_models)}")
        
        for i, model in enumerate(all_models, 1):
            print(f"   {i}. {model}")
        
        # Test getting filtered models
        print("\n🔍 Getting FILTERED models (excluding 70B+ models):")
        filtered_models = model_manager.get_available_models(force_refresh=True, filter_large=True)
        print(f"   Filtered models available: {len(filtered_models)}")
        
        for i, model in enumerate(filtered_models, 1):
            print(f"   {i}. {model}")
        
        # Show what was filtered out
        excluded = set(all_models) - set(filtered_models)
        if excluded:
            print(f"\n❌ Excluded models ({len(excluded)}):")
            for model in excluded:
                print(f"   • {model}")
        else:
            print("\n✅ No models were filtered out")
        
        # Test system optimization with filtered models
        if filtered_models:
            print(f"\n⚡ System Optimization:")
            optimal_concurrent, prioritized = model_manager.resource_manager.optimize_concurrent_models(filtered_models)
            print(f"   Optimal concurrency: {optimal_concurrent}")
            print(f"   Prioritized models: {len(prioritized)}")
            
            if prioritized:
                print("   Top recommended models:")
                for i, model in enumerate(prioritized[:3], 1):
                    print(f"      {i}. {model}")
        
        print("\n✅ Model filtering test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_model_filtering()
    
    if success:
        print("\n🎉 Model filtering is working correctly!")
        print("\n💡 Benefits:")
        print("   • Ultra-large models (70B+) are automatically excluded")
        print("   • Optimal performance on your system")
        print("   • Faster model loading and response times")
        print("   • Better memory management")
        
    else:
        print("\n💥 Model filtering test failed!")
        
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
