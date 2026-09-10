from typing import List, Optional
from backend.app.providers.base import ASRProvider, ASRSegment
from backend.app.core.config import settings

class NVIDIAASRProvider(ASRProvider):
    """
    NVIDIA Riva ASR Provider Adapter.
    Can be used when an active NVIDIA Riva gRPC / REST ASR NIM endpoint is configured.
    """
    def __init__(self, endpoint_url: Optional[str] = None):
        self.endpoint_url = endpoint_url or settings.NVIDIA_BASE_URL
        self.api_key = settings.NVIDIA_API_KEY

    def is_available(self) -> bool:
        return bool(self.api_key and self.endpoint_url)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> List[ASRSegment]:
        raise NotImplementedError("NVIDIA Riva ASR endpoint is in cloud adapter mode; use local Whisper provider for active speech recognition.")
