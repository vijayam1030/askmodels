"""
Model management module for the multi-model query application.
"""

import json
import requests
import time
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class QuestionType(Enum):
    GENERAL = "general"
    CODING = "coding"


@dataclass
class ModelResponse:
    model_name: str
    response: str
    response_time: float
    error: Optional[str] = None
    
    def is_successful(self) -> bool:
        return self.error is None


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config if file doesn't exist
            return {
                "ollama_url": "http://localhost:11434",
                "coding_models": [
                    "codellama", "deepseek-coder", "codegemma", "starcoder",
                    "magicoder", "phind-codellama", "wizardcoder", "llama3",
                    "llama3.1", "qwen2.5-coder", "granite-code"
                ],
                "request_timeout": 60,
                "max_concurrent_requests": 5
            }
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)


class OllamaModelManager:
    """Manages Ollama model interactions."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.base_url = self.config.get("ollama_url", "http://localhost:11434")
        self.available_models = []
        self.coding_models = self.config.get("coding_models", [])
        self.request_timeout = self.config.get("request_timeout", 60)
    
    def get_available_models(self) -> List[str]:
        """Fetch available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            self.available_models = [model["name"] for model in data.get("models", [])]
            return self.available_models
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching models: {e}")
            return []
    
    def get_models_for_question_type(self, question_type: QuestionType) -> List[str]:
        """Get appropriate models based on question type."""
        if question_type == QuestionType.CODING:
            # Filter for coding-capable models
            coding_capable = []
            for model in self.available_models:
                model_lower = model.lower()
                if any(coding_model in model_lower for coding_model in self.coding_models):
                    coding_capable.append(model)
            
            # If no coding-specific models found, use first few available models
            if not coding_capable and self.available_models:
                return self.available_models[:3]
            
            return coding_capable
        else:
            # For general questions, use all available models
            return self.available_models
    
    async def query_model(self, model_name: str, prompt: str, stream: bool = False) -> ModelResponse:
        """Query a specific model and return the response."""
        start_time = time.time()
        
        try:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": stream
            }
            
            if stream:
                # For streaming, we'll collect all chunks
                full_response = ""
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
                    async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                        response.raise_for_status()
                        async for line in response.content:
                            if line:
                                try:
                                    chunk_data = json.loads(line.decode('utf-8'))
                                    if 'response' in chunk_data:
                                        full_response += chunk_data['response']
                                    if chunk_data.get('done', False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                
                response_time = time.time() - start_time
                return ModelResponse(
                    model_name=model_name,
                    response=full_response,
                    response_time=response_time
                )
            else:
                # Non-streaming (original behavior)
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
                    async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                        response.raise_for_status()
                        data = await response.json()
                
                response_time = time.time() - start_time
                return ModelResponse(
                    model_name=model_name,
                    response=data.get("response", ""),
                    response_time=response_time
                )
            
        except Exception as e:
            response_time = time.time() - start_time
            return ModelResponse(
                model_name=model_name,
                response="",
                response_time=response_time,
                error=str(e)
            )

    async def query_model_streaming(self, model_name: str, prompt: str, callback=None):
        """Query a model with streaming response and optional callback for each chunk."""
        start_time = time.time()
        
        try:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": True
            }
            
            full_response = ""
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.content:
                        if line:
                            try:
                                chunk_data = json.loads(line.decode('utf-8'))
                                if 'response' in chunk_data:
                                    chunk_text = chunk_data['response']
                                    full_response += chunk_text
                                    
                                    # Call callback with streaming chunk if provided
                                    if callback:
                                        await callback(model_name, chunk_text, False)
                                
                                if chunk_data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
            
            response_time = time.time() - start_time
            
            # Call callback to indicate completion
            if callback:
                await callback(model_name, "", True)
            
            return ModelResponse(
                model_name=model_name,
                response=full_response,
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            if callback:
                await callback(model_name, f"Error: {str(e)}", True)
            
            return ModelResponse(
                model_name=model_name,
                response="",
                response_time=response_time,
                error=str(e)
            )
    
    async def query_multiple_models(self, models: List[str], prompt: str, max_concurrent: int = 3, stream: bool = True, callback=None) -> List[ModelResponse]:
        """Query multiple models concurrently with rate limiting and optional streaming."""
        # Use the configured max concurrent or the provided one
        max_concurrent = min(max_concurrent, self.config.get("max_concurrent_requests", 5))
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_query(model):
            async with semaphore:
                if stream and callback:
                    return await self.query_model_streaming(model, prompt, callback)
                else:
                    return await self.query_model(model, prompt, stream=False)
        
        # Process models in batches of max_concurrent
        results = []
        for i in range(0, len(models), max_concurrent):
            batch = models[i:i + max_concurrent]
            batch_tasks = [limited_query(model) for model in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        return results
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model."""
        try:
            response = requests.get(f"{self.base_url}/api/show", 
                                  json={"name": model_name}, 
                                  timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return {}


class PromptEnhancer:
    """Enhances prompts based on question type."""
    
    @staticmethod
    def enhance_coding_prompt(question: str) -> str:
        """Enhance prompt for coding questions."""
        return f"""You are an expert programmer. Please provide a clear, well-documented solution to the following coding question:

{question}

Please include:
- Clear explanation of the approach
- Well-commented code
- Any important considerations or edge cases
- Brief explanation of time/space complexity if applicable

Format your response clearly with sections for explanation and code."""
    
    @staticmethod
    def enhance_general_prompt(question: str) -> str:
        """Enhance prompt for general questions."""
        return f"""Please provide a comprehensive and helpful answer to the following question:

{question}

Please be clear, accurate, and provide examples where appropriate."""
    
    @classmethod
    def enhance_prompt(cls, question: str, question_type: QuestionType) -> str:
        """Enhance prompt based on question type."""
        if question_type == QuestionType.CODING:
            return cls.enhance_coding_prompt(question)
        else:
            return cls.enhance_general_prompt(question)
