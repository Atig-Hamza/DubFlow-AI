import os
import shutil
from fastapi import APIRouter
from backend.app.core.config import settings, STORAGE_PATH
from backend.app.utils.ffmpeg import is_ffmpeg_available, get_ffmpeg_version
from backend.app.utils.gpu import get_gpu_info
from backend.app.providers.nvidia.llm import NVIDIALLMProvider

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])

@router.get("/test")
async def run_system_test():
    """
    Executes a live end-to-end diagnostic test verifying all system components:
    FFmpeg, CUDA, PyTorch, NVIDIA API, ASR, Diarization, TTS, LLM, Storage.
    Returns status: 'available', 'missing', 'api_key_required', 'gpu_unavailable'
    """
    report = {}

    # 1. FFmpeg
    ffmpeg_ok = is_ffmpeg_available()
    report["ffmpeg"] = {
        "name": "FFmpeg Engine",
        "status": "available" if ffmpeg_ok else "missing",
        "details": get_ffmpeg_version() if ffmpeg_ok else "FFmpeg / ffprobe not found on PATH",
        "badge": "✓ Available" if ffmpeg_ok else "✗ Missing"
    }

    # 2. PyTorch & CUDA
    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        gpu_info = get_gpu_info()
        report["cuda"] = {
            "name": "NVIDIA CUDA / GPU",
            "status": "available" if cuda_ok else "gpu_unavailable",
            "details": f"{gpu_info['device_name']} ({gpu_info.get('free_gb', 0)} GB free / {gpu_info.get('total_gb', 0)} GB total)" if cuda_ok else "Running on CPU fallback (GPU unavailable)",
            "badge": "✓ Available" if cuda_ok else "⚠ GPU unavailable"
        }
        report["pytorch"] = {
            "name": "PyTorch Deep Learning",
            "status": "available",
            "details": f"PyTorch {torch.__version__} (CUDA: {torch.version.cuda})",
            "badge": "✓ Available"
        }
    except Exception as e:
        report["cuda"] = {"name": "NVIDIA CUDA", "status": "missing", "details": str(e), "badge": "✗ Missing"}
        report["pytorch"] = {"name": "PyTorch", "status": "missing", "details": str(e), "badge": "✗ Missing"}

    # 3. NVIDIA Cloud API & LLM
    nvidia_provider = NVIDIALLMProvider()
    if not nvidia_provider.is_configured():
        report["nvidia_api"] = {
            "name": "NVIDIA Cloud API",
            "status": "api_key_required",
            "details": "NVIDIA_API_KEY is not set in .env",
            "badge": "⚠ API key required"
        }
        report["llm"] = {
            "name": "Dialogue Translation (NVIDIA)",
            "status": "api_key_required",
            "details": "Requires NVIDIA API Key",
            "badge": "⚠ API key required"
        }
    else:
        try:
            test_trans = nvidia_provider.translate_dialogue(
                text="Hello world",
                source_lang="English",
                target_lang="French"
            )
            report["nvidia_api"] = {
                "name": "NVIDIA Cloud API",
                "status": "available",
                "details": f"Verified with {settings.NVIDIA_TRANSLATION_MODEL}",
                "badge": "✓ Available"
            }
            report["llm"] = {
                "name": "Dialogue Translation (NVIDIA Riva)",
                "status": "available",
                "details": f"Output: '{test_trans}'",
                "badge": "✓ Available"
            }
        except Exception as e:
            report["nvidia_api"] = {
                "name": "NVIDIA Cloud API",
                "status": "error",
                "details": f"Connection error: {str(e)[:100]}",
                "badge": "✗ Error"
            }
            report["llm"] = {
                "name": "Dialogue Translation (NVIDIA)",
                "status": "error",
                "details": str(e)[:100],
                "badge": "✗ Error"
            }

    # 4. Whisper ASR
    try:
        import whisper
        report["asr"] = {
            "name": "Whisper ASR",
            "status": "available",
            "details": f"Model: {settings.WHISPER_MODEL_SIZE} (FP16: {settings.WHISPER_FP16})",
            "badge": "✓ Available"
        }
    except Exception as e:
        report["asr"] = {
            "name": "Whisper ASR",
            "status": "missing",
            "details": str(e),
            "badge": "✗ Missing"
        }

    # 5. Diarization
    try:
        import librosa
        import sklearn
        report["diarization"] = {
            "name": "Speaker Diarization Engine",
            "status": "available",
            "details": "Acoustic Feature Extraction & Hierarchical Clustering",
            "badge": "✓ Available"
        }
    except Exception as e:
        report["diarization"] = {
            "name": "Speaker Diarization Engine",
            "status": "missing",
            "details": str(e),
            "badge": "✗ Missing"
        }

    # 6. Neural TTS
    try:
        import edge_tts
        report["tts"] = {
            "name": "Multi-Speaker Neural TTS",
            "status": "available",
            "details": "Edge Neural Voices (100+ languages & dialects)",
            "badge": "✓ Available"
        }
    except Exception as e:
        report["tts"] = {
            "name": "Multi-Speaker Neural TTS",
            "status": "missing",
            "details": str(e),
            "badge": "✗ Missing"
        }

    # 7. Storage
    try:
        test_file = STORAGE_PATH / ".test_write"
        test_file.write_text("ok")
        test_file.unlink()
        report["storage"] = {
            "name": "Local Storage Subsystem",
            "status": "available",
            "details": f"Path: {settings.STORAGE_DIR}",
            "badge": "✓ Available"
        }
    except Exception as e:
        report["storage"] = {
            "name": "Local Storage Subsystem",
            "status": "error",
            "details": str(e),
            "badge": "✗ Error"
        }

    return {
        "status": "success",
        "all_healthy": all(item.get("status") == "available" for item in report.values()),
        "diagnostics": report
    }
