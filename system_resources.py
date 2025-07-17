"""
System resource detection and model optimization module.
"""

import psutil
import platform
import subprocess
import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SystemResources:
    """System resource information."""
    total_ram_gb: float
    available_ram_gb: float
    cpu_cores: int
    gpu_info: List[Dict]
    platform: str
    architecture: str


@dataclass
class ModelInfo:
    """Model information with resource requirements."""
    name: str
    size_gb: float
    parameters: str
    type: str  # text, vision, code, etc.
    min_ram_gb: float
    recommended_ram_gb: float
    supports_gpu: bool


class SystemResourceManager:
    """Manages system resources and model optimization."""
    
    def __init__(self):
        self.system_info = None
        self.gpu_available = False
        self.gpu_memory_gb = 0
        self.model_size_cache = {}
        
    def detect_system_resources(self) -> SystemResources:
        """Detect available system resources."""
        # RAM information
        memory = psutil.virtual_memory()
        total_ram_gb = memory.total / (1024**3)
        available_ram_gb = memory.available / (1024**3)
        
        # CPU information
        cpu_cores = psutil.cpu_count(logical=False)
        
        # GPU information
        gpu_info = self._detect_gpu()
        
        # Platform information
        platform_name = platform.system()
        architecture = platform.machine()
        
        self.system_info = SystemResources(
            total_ram_gb=total_ram_gb,
            available_ram_gb=available_ram_gb,
            cpu_cores=cpu_cores,
            gpu_info=gpu_info,
            platform=platform_name,
            architecture=architecture
        )
        
        return self.system_info
    
    def _detect_gpu(self) -> List[Dict]:
        """Detect available GPU information."""
        gpu_info = []
        
        try:
            # Try NVIDIA GPUs first
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,memory.free', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 3:
                            gpu_info.append({
                                'name': parts[0],
                                'total_memory_mb': float(parts[1]),
                                'free_memory_mb': float(parts[2]),
                                'type': 'NVIDIA'
                            })
                            self.gpu_available = True
                            self.gpu_memory_gb += float(parts[1]) / 1024
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        try:
            # Try AMD GPUs (basic detection)
            if platform.system() == "Linux":
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                if 'AMD' in result.stdout and ('Radeon' in result.stdout or 'GPU' in result.stdout):
                    gpu_info.append({
                        'name': 'AMD GPU (detected)',
                        'total_memory_mb': 0,  # Can't easily detect without additional tools
                        'free_memory_mb': 0,
                        'type': 'AMD'
                    })
                    self.gpu_available = True
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # Try Intel GPU detection on Windows
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                    capture_output=True, text=True, timeout=5
                )
                if 'Intel' in result.stdout:
                    gpu_info.append({
                        'name': 'Intel GPU (detected)',
                        'total_memory_mb': 0,
                        'free_memory_mb': 0,
                        'type': 'Intel'
                    })
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
        
        return gpu_info
    
    def estimate_model_requirements(self, model_name: str) -> ModelInfo:
        """Estimate model resource requirements based on name."""
        # Parse model information from name
        name_lower = model_name.lower()
        
        # Extract parameter count
        parameters = "unknown"
        size_gb = 2.0  # Default small model size
        min_ram_gb = 4.0
        recommended_ram_gb = 8.0
        
        # Pattern matching for parameter counts and sizes
        patterns = [
            (r'(\d+\.?\d*)b', lambda x: float(x)),  # e.g., "7b", "13b", "70b"
            (r'(\d+)b', lambda x: float(x)),        # e.g., "7b", "13b"
            (r'(\d+\.?\d*)m', lambda x: float(x) / 1000),  # e.g., "1.5m" -> 0.0015b
        ]
        
        param_count = 0
        for pattern, converter in patterns:
            match = re.search(pattern, name_lower)
            if match:
                param_count = converter(match.group(1))
                parameters = f"{param_count}B" if param_count >= 1 else f"{param_count * 1000}M"
                break
        
        # Estimate resource requirements based on parameter count
        if param_count > 0:
            # Rough estimates: ~2GB per billion parameters for FP16
            size_gb = max(param_count * 2, 0.5)
            min_ram_gb = max(size_gb * 1.5, 2.0)  # 1.5x model size minimum
            recommended_ram_gb = max(size_gb * 2.5, 4.0)  # 2.5x for comfortable operation
        
        # Adjust for specific model types
        model_type = "text"
        supports_gpu = True
        
        if any(keyword in name_lower for keyword in ['vision', 'llava', 'clip']):
            model_type = "vision"
            recommended_ram_gb *= 1.3  # Vision models need more RAM
        elif any(keyword in name_lower for keyword in ['code', 'coder', 'coding']):
            model_type = "code"
        elif any(keyword in name_lower for keyword in ['embed', 'embedding']):
            model_type = "embedding"
            size_gb *= 0.5  # Embedding models are typically smaller
            supports_gpu = False
        
        return ModelInfo(
            name=model_name,
            size_gb=round(size_gb, 1),
            parameters=parameters,
            type=model_type,
            min_ram_gb=round(min_ram_gb, 1),
            recommended_ram_gb=round(recommended_ram_gb, 1),
            supports_gpu=supports_gpu
        )
    
    def optimize_concurrent_models(self, available_models: List[str]) -> Tuple[int, List[str]]:
        """Determine optimal number of concurrent models and prioritize models."""
        if not self.system_info:
            self.detect_system_resources()
        
        # Get model information
        model_infos = []
        for model in available_models:
            info = self.estimate_model_requirements(model)
            model_infos.append(info)
        
        # Sort models by efficiency (smaller models first for better concurrency)
        model_infos.sort(key=lambda x: (x.size_gb, x.name))
        
        # Determine optimal concurrency based on available RAM
        available_ram = self.system_info.available_ram_gb
        
        # Conservative approach: use 70% of available RAM
        usable_ram = available_ram * 0.7
        
        # Calculate optimal concurrency
        if not model_infos:
            return 1, []
        
        # Find how many of the smallest models we can run
        smallest_model = model_infos[0]
        max_concurrent_small = max(1, int(usable_ram / smallest_model.recommended_ram_gb))
        
        # Conservative limit based on CPU cores too
        max_concurrent_cpu = max(1, self.system_info.cpu_cores // 2)
        
        # Final decision
        optimal_concurrent = min(max_concurrent_small, max_concurrent_cpu, 6)  # Cap at 6
        
        # Prioritize models that fit well in memory
        prioritized_models = []
        for info in model_infos:
            if info.recommended_ram_gb <= usable_ram / optimal_concurrent:
                prioritized_models.append(info.name)
        
        # If no models fit comfortably, include at least a few smallest ones
        if not prioritized_models and model_infos:
            prioritized_models = [info.name for info in model_infos[:3]]
            optimal_concurrent = 1  # Run one at a time for large models
        
        return optimal_concurrent, prioritized_models
    
    def should_run_sequentially(self, models: List[str]) -> bool:
        """Determine if models should run sequentially instead of parallel."""
        if not self.system_info:
            self.detect_system_resources()
        
        total_estimated_ram = 0
        for model in models:
            info = self.estimate_model_requirements(model)
            total_estimated_ram += info.min_ram_gb
        
        # If total RAM requirement exceeds 80% of available RAM, run sequentially
        return total_estimated_ram > (self.system_info.available_ram_gb * 0.8)
    
    def get_resource_summary(self) -> Dict:
        """Get a summary of system resources and recommendations."""
        if not self.system_info:
            self.detect_system_resources()
        
        return {
            "system": {
                "total_ram_gb": round(self.system_info.total_ram_gb, 1),
                "available_ram_gb": round(self.system_info.available_ram_gb, 1),
                "cpu_cores": self.system_info.cpu_cores,
                "platform": self.system_info.platform,
                "architecture": self.system_info.architecture
            },
            "gpu": {
                "available": self.gpu_available,
                "total_memory_gb": round(self.gpu_memory_gb, 1) if self.gpu_memory_gb > 0 else 0,
                "devices": self.system_info.gpu_info if self.system_info else []
            },
            "recommendations": {
                "can_run_large_models": self.system_info.available_ram_gb > 16 if self.system_info else False,
                "recommended_concurrent": max(1, self.system_info.cpu_cores // 2) if self.system_info else 1,
                "use_gpu": self.gpu_available
            }
        }
    
    def print_system_info(self):
        """Print detailed system information."""
        summary = self.get_resource_summary()
        
        print("🖥️  SYSTEM RESOURCES")
        print("=" * 50)
        print(f"💾 RAM: {summary['system']['available_ram_gb']:.1f}GB available / {summary['system']['total_ram_gb']:.1f}GB total")
        print(f"🔧 CPU: {summary['system']['cpu_cores']} cores")
        print(f"🖱️  Platform: {summary['system']['platform']} ({summary['system']['architecture']})")
        
        if summary['gpu']['available']:
            print(f"🎮 GPU: Available ({summary['gpu']['total_memory_gb']:.1f}GB VRAM)" if summary['gpu']['total_memory_gb'] > 0 else "🎮 GPU: Available")
            for gpu in summary['gpu']['devices']:
                if gpu.get('total_memory_mb', 0) > 0:
                    print(f"   • {gpu['name']}: {gpu['total_memory_mb']/1024:.1f}GB")
                else:
                    print(f"   • {gpu['name']}")
        else:
            print("🎮 GPU: Not available")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   • Concurrent models: {summary['recommendations']['recommended_concurrent']}")
        print(f"   • Large models support: {'Yes' if summary['recommendations']['can_run_large_models'] else 'Limited'}")
        print(f"   • GPU acceleration: {'Available' if summary['recommendations']['use_gpu'] else 'CPU only'}")
    
    def get_real_time_usage(self) -> Dict:
        """Get real-time system resource usage."""
        try:
            import time
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_used_gb = (memory.total - memory.available) / (1024**3)
            memory_percent = memory.percent
            
            # Disk usage (for the main drive)
            try:
                disk = psutil.disk_usage('/' if platform.system() != 'Windows' else 'C:')
                disk_percent = (disk.used / disk.total) * 100
                disk_info = {
                    'total_gb': round(disk.total / (1024**3), 1),
                    'used_gb': round(disk.used / (1024**3), 1),
                    'free_gb': round(disk.free / (1024**3), 1),
                    'percent': round(disk_percent, 1)
                }
            except:
                disk_info = {'error': 'Cannot access disk info'}
            
            # Network stats
            try:
                network = psutil.net_io_counters()
                network_info = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            except:
                network_info = {'error': 'Cannot access network info'}
            
            # Process count
            try:
                process_count = len(psutil.pids())
            except:
                process_count = 0
            
            # GPU usage (if available)
            gpu_usage = self._get_gpu_usage()
            
            return {
                'timestamp': time.time(),
                'cpu': {
                    'percent': round(cpu_percent, 1),
                    'per_core': [round(core, 1) for core in cpu_per_core],
                    'cores': len(cpu_per_core)
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 1),
                    'available_gb': round(memory.available / (1024**3), 1),
                    'used_gb': round(memory_used_gb, 1),
                    'percent': round(memory_percent, 1)
                },
                'disk': disk_info,
                'network': network_info,
                'processes': process_count,
                'gpu': gpu_usage
            }
            
        except Exception as e:
            print(f"Error getting real-time usage: {e}")
            return {
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _get_gpu_usage(self) -> List[Dict]:
        """Get GPU usage information."""
        gpu_usage = []
        
        try:
            # Try nvidia-smi for NVIDIA GPUs
            result = subprocess.run([
                'nvidia-smi', 
                '--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = [part.strip() for part in line.split(',')]
                        if len(parts) >= 6:
                            try:
                                gpu_usage.append({
                                    'index': int(parts[0]),
                                    'name': parts[1],
                                    'utilization_percent': float(parts[2]) if parts[2] != 'N/A' else 0,
                                    'memory_used_mb': float(parts[3]) if parts[3] != 'N/A' else 0,
                                    'memory_total_mb': float(parts[4]) if parts[4] != 'N/A' else 0,
                                    'temperature_c': float(parts[5]) if parts[5] != 'N/A' else 0
                                })
                            except ValueError:
                                continue
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # nvidia-smi not available or failed
            pass
        
        # If no NVIDIA GPUs found, try other methods or return basic info
        if not gpu_usage and self.system_info and self.system_info.gpu_info:
            for i, gpu in enumerate(self.system_info.gpu_info):
                gpu_usage.append({
                    'index': i,
                    'name': gpu.get('name', 'Unknown GPU'),
                    'utilization_percent': 0,  # Cannot get real-time usage without nvidia-smi
                    'memory_used_mb': 0,
                    'memory_total_mb': gpu.get('memory_gb', 0) * 1024,
                    'temperature_c': 0,
                    'note': 'Real-time usage unavailable'
                })
        
        return gpu_usage


# Global instance
resource_manager = SystemResourceManager()
