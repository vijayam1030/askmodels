import gradio as gr
import requests
import json
import time

def test_gradio():
    """Test basic Gradio functionality"""
    print("Testing basic Gradio functionality...")
    
    def simple_function(text):
        return f"You said: {text}"
    
    # Create a simple interface
    with gr.Blocks(title="Test") as demo:
        gr.Markdown("# Test Interface")
        
        input_box = gr.Textbox(label="Input", value="Hello World!")
        output_box = gr.Textbox(label="Output")
        button = gr.Button("Submit")
        
        button.click(simple_function, inputs=input_box, outputs=output_box)
    
    print("Simple interface created successfully!")
    return demo

def test_backend_connection():
    """Test connection to Flask backend"""
    print("Testing Flask backend connection...")
    
    try:
        response = requests.get("http://localhost:5000/api/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend connection successful! Found {len(data.get('models', []))} models")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Gradio diagnostics...")
    
    # Test 1: Basic Gradio functionality
    try:
        demo = test_gradio()
        print("✅ Gradio interface creation: PASSED")
    except Exception as e:
        print(f"❌ Gradio interface creation: FAILED - {e}")
        exit(1)
    
    # Test 2: Backend connection
    backend_ok = test_backend_connection()
    
    # Test 3: Launch the simple interface
    print("\n📋 Diagnostics Summary:")
    print(f"- Gradio version: {gr.__version__}")
    print(f"- Backend connection: {'✅ OK' if backend_ok else '❌ FAILED'}")
    print(f"- Simple interface: ✅ OK")
    
    print("\n🚀 Launching simple test interface...")
    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7861,  # Different port to avoid conflicts
            share=False,
            debug=True,
            show_error=True
        )
    except Exception as e:
        print(f"❌ Launch failed: {e}")
