import os
from pathlib import Path
from typing import Dict, Any, List
from backend.app.core.config import SEGMENTS_DIR
from backend.app.core.logging import logger
from backend.app.providers.local.tts import LocalEdgeTTSProvider

class TTSService:
    """
    Synthesizes translated dialogue into distinct AI voices per speaker.
    Guarantees consistent speaker-to-voice assignment.
    """
    def __init__(self):
        self.provider = LocalEdgeTTSProvider()

    async def generate_line_audio(
        self,
        project_id: str,
        line_id: str,
        text: str,
        voice_id: str,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> str:
        """
        Generates individual line speech audio and saves into storage/segments.
        """
        output_filename = f"{project_id}_{line_id}_raw.wav"
        output_path = str(SEGMENTS_DIR / output_filename)

        logger.info(f"[TTS] Generating speech for line {line_id} with voice {voice_id}...")
        await self.provider.generate_voice(
            text=text,
            voice_id=voice_id,
            output_path=output_path,
            rate=rate,
            pitch=pitch
        )
        return output_path

    async def generate_preview_voice(self, voice_id: str, output_path: str, sample_text: str = None) -> str:
        return await self.provider.generate_preview(voice_id, output_path, sample_text)

tts_service = TTSService()
