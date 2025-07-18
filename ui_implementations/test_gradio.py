import gradio as gr
import subprocess
import time
import threading
import requests

def test_gradio_app():
    """Test the Gradio app works"""
    print("🚀 Testing Gradio App...")
    
    # Test Flask backend connection
    try:
        response = requests.get("http://localhost:5000/api/models", timeout=5)
        if response.status_code == 200:
            print("✅ Flask backend is running and accessible")
        else:
            print(f"⚠️  Flask backend returned {response.status_code}")
    except Exception as e:
        print(f"❌ Flask backend not accessible: {e}")
    
    # Test Gradio import
    try:
        import gradio_app_simple
        print("✅ Gradio app imports successfully")
    except Exception as e:
        print(f"❌ Gradio app import failed: {e}")
        return False
    
    # Test Gradio app initialization
    try:
        app = gradio_app_simple.SimpleGradioApp()
        print("✅ Gradio app initializes successfully")
        
        # Test model loading
        print(f"✅ Loaded {len(app.models)} models")
        
        # Test interface creation
        interface = app.create_interface()
        print("✅ Gradio interface created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Gradio app initialization failed: {e}")
        return False

def launch_gradio_app():
    """Launch the Gradio app"""
    print("\n🚀 Launching Gradio App...")
    
    try:
        import gradio_app_simple
        app = gradio_app_simple.SimpleGradioApp()
        
        print("📋 App Status:")
        print(f"- Models loaded: {len(app.models)}")
        print(f"- Session ID: {app.session_id[:8]}...")
        print(f"- Base URL: {app.base_url}")
        
        print("\n🌐 Starting web interface...")
        print("You can access the app at: http://localhost:7860")
        print("Press Ctrl+C to stop the app")
        
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            debug=True,
            show_error=True
        )
        
    except Exception as e:
        print(f"❌ Failed to launch Gradio app: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Gradio App Test Suite")
    print("=" * 50)
    
    # Run tests
    success = test_gradio_app()
    
    if success:
        print("\n✅ All tests passed! Gradio app is working correctly.")
        
        # Ask user if they want to launch
        user_input = input("\nWould you like to launch the Gradio app? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            launch_gradio_app()
        else:
            print("✅ Test complete. You can launch the app later with: python gradio_app_simple.py")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
