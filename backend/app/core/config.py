import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Root directory of DubFlow AI project
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "DubFlow AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # NVIDIA Cloud APIs
    NVIDIA_API_KEY: str = "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"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_TRANSLATION_MODEL: str = "nvidia/riva-translate-4b-instruct-v2"
    NVIDIA_LLM_MODEL: str = "nvidia/riva-translate-4b-instruct-v2"

    # Storage Paths
    STORAGE_DIR: str = str(BASE_DIR / "storage")
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/storage/dubflow.db"

    # Hardware & Model Optimizations for RTX A2000 4GB VRAM
    DEVICE: str = "cuda"
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_FP16: bool = True
    MAX_VRAM_GB: float = 3.8
    AUTO_RELEASE_CUDA_CACHE: bool = True

    class Config:
        env_file = str(BASE_DIR / ".env")
        extra = "allow"

settings = Settings()

# Setup explicit storage directories as per spec
STORAGE_PATH = Path(settings.STORAGE_DIR)
UPLOADS_DIR = STORAGE_PATH / "uploads"
AUDIO_DIR = STORAGE_PATH / "audio"
SEGMENTS_DIR = STORAGE_PATH / "segments"
VOICES_DIR = STORAGE_PATH / "voices"
OUTPUTS_DIR = STORAGE_PATH / "outputs"
PROJECTS_DIR = STORAGE_PATH / "projects"

for directory in [UPLOADS_DIR, AUDIO_DIR, SEGMENTS_DIR, VOICES_DIR, OUTPUTS_DIR, PROJECTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
