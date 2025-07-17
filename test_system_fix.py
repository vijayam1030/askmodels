#!/usr/bin/env python3
"""
Quick test to verify system resource access is working correctly.
"""

from config import ConfigManager
from models import OllamaModelManager

def test_system_resources():
    """Test system resource access."""
    print("🧪 Testing System Resource Access")
    print("=" * 40)
    
    try:
        # Initialize components
        config_manager = ConfigManager()
        model_manager = OllamaModelManager(config_manager)
        
        # Access system info
        info = model_manager.resource_manager.system_info
        
        print("✅ System info accessed successfully:")
        print(f"   💾 RAM: {info.available_ram_gb:.1f}GB / {info.total_ram_gb:.1f}GB")
        print(f"   🔧 CPU: {info.cpu_cores} cores")
        print(f"   🎮 GPU: {len(info.gpu_info)} detected")
        
        if info.gpu_info:
            for i, gpu in enumerate(info.gpu_info):
                print(f"      {i+1}. {gpu.get('name', 'Unknown')} ({gpu.get('memory_gb', 0):.1f}GB)")
        
        print("\n✅ No attribute errors - system resource access working correctly!")
        return True
        
    except AttributeError as e:
        print(f"❌ Attribute error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

if __name__ == "__main__":
    success = test_system_resources()
    if success:
        print("\n🎉 System resource test passed!")
    else:
        print("\n💥 System resource test failed!")
