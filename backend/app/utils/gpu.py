import gc
from typing import Dict, Any

def get_optimal_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"

def clean_vram():
    """
    Explicitly forces garbage collection and releases PyTorch CUDA cache.
    Crucial for 4GB VRAM GPU (RTX A2000) lifecycle.
    """
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass

def get_gpu_info() -> Dict[str, Any]:
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            total_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            allocated_mem = torch.cuda.memory_allocated(0) / (1024 ** 3)
            cached_mem = torch.cuda.memory_reserved(0) / (1024 ** 3)
            free_mem = total_mem - cached_mem
            return {
                "available": True,
                "device_name": device_name,
                "total_gb": round(total_mem, 2),
                "allocated_gb": round(allocated_mem, 2),
                "cached_gb": round(cached_mem, 2),
                "free_gb": round(free_mem, 2),
            }
    except Exception as e:
        return {"available": False, "error": str(e)}
    
    return {
        "available": False,
        "device_name": "CPU",
        "total_gb": 0,
        "free_gb": 0
    }
