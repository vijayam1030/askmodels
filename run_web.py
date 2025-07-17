#!/usr/bin/env python3
"""
Simple launcher for the Multi-Model Query Web Application
"""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed."""
    required = ['flask', 'flask_socketio']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def install_dependencies():
    """Install missing dependencies."""
    print("📦 Installing web UI dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main launcher function."""
    print("🚀 Multi-Model Query Web UI Launcher")
    print("=" * 50)
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"📦 Missing dependencies: {', '.join(missing)}")
        install_choice = input("Install missing dependencies? (y/N): ").strip().lower()
        if install_choice in ['y', 'yes']:
            if not install_dependencies():
                print("❌ Cannot start without required dependencies")
                return
        else:
            print("❌ Cannot start without required dependencies")
            return
    
    print("✅ All dependencies available")
    print("🌐 Starting web server...")
    print("📱 The web interface will open automatically")
    print("🔗 Manual URL: http://localhost:5000")
    print("\n⚠️  Make sure Ollama is running before using the application!")
    print("   Run: ollama serve")
    print("\n📋 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Wait a moment then open browser
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:5000')
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the web application
    try:
        from web_app import app, socketio
        socketio.run(app, debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Web server stopped")
    except Exception as e:
        print(f"\n❌ Error starting web server: {e}")

if __name__ == "__main__":
    main()
