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
from system_resources import SystemResourceManager, resource_manager


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
    """Manages Ollama model interactions with system resource optimization."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.base_url = self.config.get("ollama_url", "http://localhost:11434")
        self.available_models = []
        self.coding_models = self.config.get("coding_models", [])
        self.request_timeout = self.config.get("request_timeout", 60)
        self.resource_manager = resource_manager
        self.last_model_refresh = 0
        self.model_refresh_interval = 30  # Refresh every 30 seconds
        
        # Initialize system resources
        self.resource_manager.detect_system_resources()
    
    def should_refresh_models(self) -> bool:
        """Check if models should be refreshed."""
        return (time.time() - self.last_model_refresh) > self.model_refresh_interval
    
    def _filter_large_models(self, models: List[str]) -> List[str]:
        """Filter out ultra-large models (70B+ parameters) for better performance."""
        filtered_models = []
        excluded_models = []
        
        for model in models:
            model_lower = model.lower()
            
            # Check for ultra-large model indicators
            is_ultra_large = any([
                '70b' in model_lower,
                '72b' in model_lower,
                '405b' in model_lower,
                'llama3.1:70b' in model_lower,
                'llama3.2:70b' in model_lower,
                'qwen2.5:72b' in model_lower,
                'codellama:70b' in model_lower
            ])
            
            if is_ultra_large:
                excluded_models.append(model)
            else:
                filtered_models.append(model)
        
        if excluded_models:
            print(f"⚠️  Filtered out {len(excluded_models)} ultra-large models for optimal performance")
            for model in excluded_models:
                print(f"   • {model}")
        
        return filtered_models
    
    def get_available_models(self, force_refresh: bool = False, filter_large: bool = True) -> List[str]:
        """Fetch available models from Ollama with automatic refresh and optional filtering."""
        if force_refresh or self.should_refresh_models() or not self.available_models:
            try:
                print("🔄 Refreshing model list from Ollama...")
                response = requests.get(f"{self.base_url}/api/tags", timeout=10)
                response.raise_for_status()
                data = response.json()
                
                raw_models = [model["name"] for model in data.get("models", [])]
                
                # Apply filtering if requested
                if filter_large:
                    new_models = self._filter_large_models(raw_models)
                else:
                    new_models = raw_models
                
                # Check for changes
                if set(new_models) != set(self.available_models):
                    print(f"📊 Model list updated: {len(new_models)} models available")
                    if filter_large and len(raw_models) != len(new_models):
                        print(f"   (Filtered from {len(raw_models)} total models)")
                    
                    if new_models != self.available_models:
                        added = set(new_models) - set(self.available_models)
                        removed = set(self.available_models) - set(new_models)
                        if added:
                            print(f"   ➕ Added: {', '.join(added)}")
                        if removed:
                            print(f"   ➖ Removed: {', '.join(removed)}")
                
                self.available_models = new_models
                self.last_model_refresh = time.time()
                
                # Optimize for current system
                self._optimize_for_system()
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching models: {e}")
                if not self.available_models:
                    return []
        
        return self.available_models
    
    def _optimize_for_system(self):
        """Optimize settings based on current system resources and available models."""
        if not self.available_models:
            return
        
        # Get system optimization recommendations
        optimal_concurrent, _ = self.resource_manager.optimize_concurrent_models(self.available_models)
        
        # Update configuration based on system capabilities
        current_concurrent = self.config.get("max_concurrent_requests", 3)
        if optimal_concurrent != current_concurrent:
            print(f"🎯 Optimizing concurrency: {current_concurrent} → {optimal_concurrent} (based on system resources)")
            self.config.config["max_concurrent_requests"] = optimal_concurrent
        
        # Check if we should warn about large models
        large_models = []
        for model in self.available_models:
            model_info = self.resource_manager.estimate_model_requirements(model)
            if model_info.recommended_ram_gb > self.resource_manager.system_info.available_ram_gb * 0.6:
                large_models.append(f"{model} (~{model_info.recommended_ram_gb}GB)")
        
        if large_models:
            print(f"⚠️  Large models detected (may run slowly): {', '.join(large_models[:3])}")
            if len(large_models) > 3:
                print(f"   ... and {len(large_models) - 3} more")
    
    def get_models_for_question_type(self, question_type: QuestionType) -> List[str]:
        """Get appropriate models based on question type and system capabilities."""
        # Always refresh model list
        available = self.get_available_models()
        
        if question_type == QuestionType.CODING:
            # Filter for coding-capable models
            coding_capable = []
            for model in available:
                model_lower = model.lower()
                if any(coding_model in model_lower for coding_model in self.coding_models):
                    coding_capable.append(model)
            
            # Optimize based on system resources
            if coding_capable:
                _, prioritized = self.resource_manager.optimize_concurrent_models(coding_capable)
                return prioritized if prioritized else coding_capable[:3]
            
            # Fallback to general models if no coding models found
            if available:
                _, prioritized = self.resource_manager.optimize_concurrent_models(available)
                return prioritized[:3] if prioritized else available[:3]
            
            return []
        else:
            # For general questions, use all available models but optimize order
            if available:
                _, prioritized = self.resource_manager.optimize_concurrent_models(available)
                return prioritized if prioritized else available
            return []
    
    def get_optimal_concurrency(self, models: List[str]) -> int:
        """Get optimal concurrency for given models."""
        if not models:
            return 1
        
        # Check if models should run sequentially
        if self.resource_manager.should_run_sequentially(models):
            print("🔄 Running models sequentially due to memory constraints")
            return 1
        
        # Get system-optimized concurrency
        optimal_concurrent, _ = self.resource_manager.optimize_concurrent_models(models)
        configured_max = self.config.get("max_concurrent_requests", 3)
        
        return min(optimal_concurrent, configured_max, len(models))
    
    def print_model_analysis(self, models: List[str]):
        """Print analysis of models and system suitability."""
        print(f"\n📋 MODEL ANALYSIS ({len(models)} models)")
        print("-" * 50)
        
        total_estimated_ram = 0
        for model in models:
            model_info = self.resource_manager.estimate_model_requirements(model)
            total_estimated_ram += model_info.min_ram_gb
            
            status = "✅"
            if model_info.min_ram_gb > self.resource_manager.system_info.available_ram_gb * 0.8:
                status = "⚠️"
            elif model_info.min_ram_gb > self.resource_manager.system_info.available_ram_gb:
                status = "❌"
            
            print(f"{status} {model}")
            print(f"   Size: ~{model_info.size_gb}GB, RAM: {model_info.min_ram_gb}GB min, Type: {model_info.type}")
        
        available_ram = self.resource_manager.system_info.available_ram_gb
        print(f"\n💾 Total estimated RAM: {total_estimated_ram:.1f}GB / {available_ram:.1f}GB available")
        
        if total_estimated_ram > available_ram * 0.8:
            print("⚠️  High memory usage - models will run sequentially")
        elif total_estimated_ram > available_ram * 0.6:
            print("⚠️  Moderate memory usage - reduced concurrency recommended")
        else:
            print("✅ Memory usage looks good for parallel execution")
    
    async def query_model(self, model_name: str, prompt: str, stream: bool = False) -> ModelResponse:
        """Query a specific model and return the response."""
        start_time = time.time()
        
        try:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": stream
            }
            
            timeout = aiohttp.ClientTimeout(total=self.request_timeout, connect=10, sock_read=30)
            
            if stream:
                # For streaming, we'll collect all chunks
                full_response = ""
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                        if response.status == 404:
                            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time, 
                                               error=f"Model '{model_name}' not found")
                        
                        if response.status != 200:
                            error_text = await response.text()
                            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time,
                                               error=f"HTTP {response.status}: {error_text[:100]}")
                        
                        response.raise_for_status()
                        async for line in response.content:
                            if line:
                                try:
                                    line_text = line.decode('utf-8').strip()
                                    if not line_text:
                                        continue
                                    chunk_data = json.loads(line_text)
                                    if 'error' in chunk_data:
                                        return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time,
                                                           error=chunk_data['error'])
                                    if 'response' in chunk_data:
                                        full_response += chunk_data['response']
                                    if chunk_data.get('done', False):
                                        break
                                except (json.JSONDecodeError, UnicodeDecodeError):
                                    continue
                
                return ModelResponse(model_name=model_name, response=full_response, response_time=time.time() - start_time)
            else:
                # Non-streaming (original behavior)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                        if response.status == 404:
                            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time,
                                               error=f"Model '{model_name}' not found")
                        
                        if response.status != 200:
                            error_text = await response.text()
                            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time,
                                               error=f"HTTP {response.status}: {error_text[:100]}")
                        
                        response.raise_for_status()
                        data = await response.json()
                        
                        if 'error' in data:
                            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time,
                                               error=data['error'])
                
                return ModelResponse(model_name=model_name, response=data.get("response", ""), response_time=time.time() - start_time)
            
        except asyncio.TimeoutError:
            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time,
                               error=f"Timeout after {self.request_timeout}s")
        except aiohttp.ClientConnectorError:
            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time,
                               error="Cannot connect to Ollama server")
        except Exception as e:
            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time,
                               error=f"{type(e).__name__}: {str(e)}")

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
            timeout = aiohttp.ClientTimeout(total=self.request_timeout, connect=10, sock_read=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                        if response.status == 404:
                            error_msg = f"Model '{model_name}' not found"
                            if callback:
                                await callback(model_name, f"Error: {error_msg}", True)
                            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time, error=error_msg)
                        
                        if response.status != 200:
                            error_text = await response.text()
                            error_msg = f"HTTP {response.status}: {error_text[:100]}"
                            if callback:
                                await callback(model_name, f"Error: {error_msg}", True)
                            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time, error=error_msg)
                        
                        response.raise_for_status()
                        
                        async for line in response.content:
                            if line:
                                try:
                                    line_text = line.decode('utf-8').strip()
                                    if not line_text:
                                        continue
                                        
                                    chunk_data = json.loads(line_text)
                                    
                                    # Check for error in response
                                    if 'error' in chunk_data:
                                        error_msg = chunk_data['error']
                                        if callback:
                                            await callback(model_name, f"Error: {error_msg}", True)
                                        return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time, error=error_msg)
                                    
                                    if 'response' in chunk_data:
                                        chunk_text = chunk_data['response']
                                        full_response += chunk_text
                                        
                                        # Call callback with streaming chunk if provided
                                        if callback:
                                            await callback(model_name, chunk_text, False)
                                    
                                    if chunk_data.get('done', False):
                                        break
                                        
                                except json.JSONDecodeError as je:
                                    print(f"JSON decode error for {model_name}: {je} - Line: {line_text}")
                                    continue
                                except UnicodeDecodeError as ue:
                                    print(f"Unicode decode error for {model_name}: {ue}")
                                    continue
                        
                        if not full_response:
                            error_msg = "No response received from model"
                            if callback:
                                await callback(model_name, f"Error: {error_msg}", True)
                            return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time, error=error_msg)
                
                except asyncio.TimeoutError:
                    error_msg = f"Timeout after {self.request_timeout}s"
                    if callback:
                        await callback(model_name, f"Error: {error_msg}", True)
                    return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time, error=error_msg)
                
                except aiohttp.ClientConnectorError:
                    error_msg = "Cannot connect to Ollama server"
                    if callback:
                        await callback(model_name, f"Error: {error_msg}", True)
                    return ModelResponse(model_name=model_name, response="", response_time=time.time() - start_time, error=error_msg)
            
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
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"Unexpected error for {model_name}: {error_msg}")
            
            if callback:
                await callback(model_name, f"Error: {error_msg}", True)
            
            return ModelResponse(
                model_name=model_name,
                response="",
                response_time=response_time,
                error=error_msg
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
