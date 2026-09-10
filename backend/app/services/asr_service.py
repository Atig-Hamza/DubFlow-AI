import asyncio
from typing import List, Optional, Dict, Any
from backend.app.core.logging import logger
from backend.app.providers.base import ASRSegment
from backend.app.providers.local.asr import LocalWhisperASRProvider

class ASRService:
    """
    Speech recognition service orchestrating speech-to-text with timestamps and confidence scores.
    """
    def __init__(self):
        self.provider = LocalWhisperASRProvider()

    async def transcribe_audio(self, audio_path: str, language: Optional[str] = None) -> List[ASRSegment]:
        logger.info(f"[ASR] Starting speech transcription for {audio_path}")
        # Run synchronous Whisper inference in threadpool so event loop is never blocked
        loop = asyncio.get_running_loop()
        segments = await loop.run_in_executor(None, self.provider.transcribe, audio_path, language)
        return segments

asr_service = ASRService()
