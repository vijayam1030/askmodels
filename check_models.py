#!/usr/bin/env python3
"""
Quick model checker
"""

import requests
import json

def check_models():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            print(f"Available models ({len(models)}):")
            for model in models:
                print(f"  • {model}")
            return models
        else:
            print(f"Error: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
    return []

if __name__ == "__main__":
    check_models()
