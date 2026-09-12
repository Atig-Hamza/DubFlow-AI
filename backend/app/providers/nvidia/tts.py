from typing import List, Dict, Any, Optional
from backend.app.providers.base import TTSProvider
from backend.app.core.config import settings

class NVIDIATTSProvider(TTSProvider):
    """
    NVIDIA FastPitch / HiFi-GAN Cloud TTS Provider Adapter.
    Can be used when an active NVIDIA Riva TTS NIM endpoint is deployed.
    """
    def __init__(self, endpoint_url: Optional[str] = None):
        self.endpoint_url = endpoint_url or settings.NVIDIA_BASE_URL
        self.api_key = settings.NVIDIA_API_KEY

    def is_available(self) -> bool:
        return False

    async def generate_voice(self, text: str, voice_id: str, output_path: str, rate: str = "+0%", pitch: str = "+0Hz") -> str:
        raise NotImplementedError("NVIDIA TTS NIM endpoint not currently reachable; falling back to local neural TTS provider.")

    async def generate_preview(self, voice_id: str, output_path: str, sample_text: Optional[str] = None) -> str:
        raise NotImplementedError("NVIDIA TTS preview not configured.")

    def get_available_voices(self, language: str) -> List[Dict[str, Any]]:
        return []
