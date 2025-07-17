#!/usr/bin/env python3
"""
Setup script for Multi-Model Query Application
Helps verify the environment and setup.
"""

import sys
import subprocess
import json
import requests
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['requests', 'aiohttp']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} is missing")
    
    return missing


def install_dependencies():
    """Install missing dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def check_ollama():
    """Check if Ollama is running and has models."""
    print("🔍 Checking Ollama connection...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        
        if models:
            print(f"✅ Ollama is running with {len(models)} models:")
            for model in models[:5]:  # Show first 5 models
                print(f"   • {model['name']}")
            if len(models) > 5:
                print(f"   ... and {len(models) - 5} more")
            return True
        else:
            print("⚠️  Ollama is running but no models are installed")
            print("   Run: ollama pull llama3.1")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama")
        print("   Make sure Ollama is installed and running: ollama serve")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking Ollama: {e}")
        return False


def create_config_if_missing():
    """Create config.json if it doesn't exist."""
    config_path = Path("config.json")
    
    if config_path.exists():
        print("✅ config.json exists")
        return True
    
    print("📝 Creating config.json...")
    default_config = {
        "ollama_url": "http://localhost:11434",
        "coding_models": [
            "codellama", "deepseek-coder", "codegemma", "starcoder",
            "magicoder", "phind-codellama", "wizardcoder", "llama3",
            "llama3.1", "qwen2.5-coder", "granite-code"
        ],
        "request_timeout": 60,
        "max_concurrent_requests": 5
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print("✅ config.json created")
        return True
    except Exception as e:
        print(f"❌ Failed to create config.json: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Multi-Model Query Application Setup")
    print("=" * 50)
    
    all_good = True
    
    # Check Python version
    if not check_python_version():
        all_good = False
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"\n📦 Missing dependencies: {', '.join(missing_deps)}")
        install_choice = input("Install missing dependencies? (y/N): ").strip().lower()
        if install_choice in ['y', 'yes']:
            if not install_dependencies():
                all_good = False
        else:
            all_good = False
    
    # Create config if missing
    if not create_config_if_missing():
        all_good = False
    
    # Check Ollama
    if not check_ollama():
        all_good = False
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("🎉 Setup complete! You can now run: python main.py")
    else:
        print("⚠️  Setup incomplete. Please resolve the issues above.")
        print("\nCommon solutions:")
        print("• Install Ollama: https://ollama.ai")
        print("• Start Ollama: ollama serve")
        print("• Install models: ollama pull llama3.1")
        print("• Install dependencies: pip install -r requirements.txt")


if __name__ == "__main__":
    main()
