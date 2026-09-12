import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import edge_tts
from backend.app.core.logging import logger
from backend.app.providers.base import TTSProvider
from backend.app.services.language_service import language_manager
from backend.app.utils.ffmpeg import run_ffmpeg

class LocalEdgeTTSProvider(TTSProvider):
    """
    Local Neural TTS Provider using Edge-TTS.
    Produces broadcast-quality studio voices in 100+ languages and dialects with pitch/rate control.
    """
    def __init__(self):
        pass

    async def generate_voice(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> str:
        """
        Synthesizes text into high-fidelity speech and saves as standard WAV audio.
        """
        if not text or not text.strip():
            raise ValueError("Cannot synthesize empty text.")

        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Temporary MP3 path as edge-tts natively outputs audio/mpeg
        temp_mp3 = str(output_path) + ".temp.mp3"

        logger.info(f"[TTS] Synthesizing ({voice_id}, rate={rate}, pitch={pitch}): '{text[:40]}...'")
        
        try:
            communicate = edge_tts.Communicate(
                text=text.strip(),
                voice=voice_id,
                rate=rate,
                pitch=pitch
            )
            await communicate.save(temp_mp3)

            # 5-Stage Broadcast Studio Vocal Mastering Chain:
            # 1. High-pass filter at 75Hz (removes low-end sub rumble)
            # 2. Parametric warmth EQ at 220Hz (+2.5dB body)
            # 3. Presence & intelligibility EQ at 3400Hz (+3.5dB clarity)
            # 4. Air sheen EQ at 8000Hz (+2.0dB brilliance)
            # 5. Broadcast compressor (threshold -18dB, ratio 3:1, makeup +4dB)
            # 6. EBU R128 Loudness Normalization (-16 LUFS broadcast standard)
            mastering_chain = (
                "highpass=f=75,"
                "equalizer=f=220:t=q:w=1.2:g=2.5,"
                "equalizer=f=3400:t=q:w=1.5:g=3.5,"
                "equalizer=f=8000:t=q:w=1.0:g=2.0,"
                "acompressor=threshold=-18dB:ratio=3.0:attack=15:release=120:makeup=4dB,"
                "loudnorm=I=-16:TP=-1.0:LRA=7"
            )

            # Master speech to 24kHz Mono WAV for clean timing sync and mixing
            await run_ffmpeg([
                "-i", temp_mp3,
                "-af", mastering_chain,
                "-ar", "24000",
                "-ac", "1",
                output_path
            ])

            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)

            return output_path
        except Exception as e:
            if os.path.exists(temp_mp3):
                try:
                    os.remove(temp_mp3)
                except Exception:
                    pass
            logger.error(f"[TTS] Failed to synthesize speech: {e}")
            raise e

    async def generate_preview(self, voice_id: str, output_path: str, sample_text: Optional[str] = None) -> str:
        """
        Generates a quick voice preview sample in the voice's native language.
        """
        if not sample_text:
            vid = voice_id.lower()
            if vid.startswith("ar-"):
                sample_text = "مرحباً بكم، هذا نموذج لصوتي الطبيعي في داب فلو للدبلجة الذكية."
            elif vid.startswith("fr-"):
                sample_text = "Bonjour, ceci est un aperçu de ma voix de studio pour le doublage DubFlow."
            elif vid.startswith("es-"):
                sample_text = "Hola, esta es una muestra natural de mi voz para el doblaje en DubFlow."
            elif vid.startswith("de-"):
                sample_text = "Hallo, dies ist eine Hörprobe meiner Stimme für DubFlow."
            elif vid.startswith("tr-"):
                sample_text = "Merhaba, bu DubFlow için yapay zeka ses örneğidir."
            elif vid.startswith("it-"):
                sample_text = "Ciao, questo è un esempio della mia voce per DubFlow."
            elif vid.startswith("pt-"):
                sample_text = "Olá, esta é uma demonstração da minha voz para o DubFlow."
            else:
                sample_text = "Hello! This is a studio voice preview for DubFlow video dubbing."
        return await self.generate_voice(sample_text, voice_id, output_path)

    def get_available_voices(self, language: str) -> List[Dict[str, Any]]:
        meta = language_manager.get_language(language)
        if meta:
            return meta.voices
        return []
