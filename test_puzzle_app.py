#!/usr/bin/env python3
"""
Simple startup script to test the puzzle functionality
"""

import os
import sys
import webbrowser
import time
from threading import Timer

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    """Open browser after a short delay"""
    print("Opening browser...")
    webbrowser.open('http://localhost:5000/dashboard-test')

def main():
    """Main function to start the app"""
    print("Starting Flask app for puzzle testing...")
    
    # Import and run the Flask app
    from unified_app import app, socketio
    
    # Schedule browser opening
    Timer(2.0, open_browser).start()
    
    # Start the Flask app
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting app: {e}")

if __name__ == "__main__":
    main()
