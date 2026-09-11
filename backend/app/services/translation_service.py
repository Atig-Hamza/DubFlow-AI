import asyncio
from typing import List, Dict, Any, Optional
from backend.app.core.logging import logger
from backend.app.providers.nvidia.llm import NVIDIALLMProvider

class TranslationService:
    """
    Context-aware dialogue translation using NVIDIA AI endpoints.
    Supplies conversational context (preceding/following lines, speaker characteristics, duration constraints).
    """
    def __init__(self):
        self.provider = NVIDIALLMProvider()

    async def translate_project_transcript(
        self,
        lines: List[Dict[str, Any]],
        source_lang: str,
        target_lang: str,
        speakers_map: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Translates all dialogue lines sequentially with surrounding context and duration awareness.
        """
        logger.info(f"[TRANSLATION] Translating {len(lines)} lines from {source_lang} to {target_lang}...")
        
        loop = asyncio.get_running_loop()
        translated_lines = []

        for i, line in enumerate(lines):
            original = line.get("original", line.get("text", ""))
            start = line.get("start", 0.0)
            end = line.get("end", 0.0)
            target_duration = end - start
            speaker_tag = line.get("speaker", line.get("speaker_id", "speaker_01"))

            # Retrieve speaker info if available
            speaker_info = None
            if speakers_map and speaker_tag in speakers_map:
                spk = speakers_map[speaker_tag]
                gender = getattr(spk, "gender_detected", "neutral")
                speaker_info = f"{speaker_tag}, {gender} voice"

            # Context: previous and following dialogue
            prev_context = lines[i - 1].get("original", lines[i - 1].get("text", "")) if i > 0 else None
            next_context = lines[i + 1].get("original", lines[i + 1].get("text", "")) if i < len(lines) - 1 else None

            # Execute translation via provider
            try:
                translated_text = await loop.run_in_executor(
                    None,
                    self.provider.translate_dialogue,
                    original,
                    source_lang,
                    target_lang,
                    prev_context,
                    next_context,
                    speaker_info,
                    target_duration
                )
            except Exception as e:
                logger.warning(f"[TRANSLATION] Line {i+1} translation error ({e}), keeping original text.")
                translated_text = original

            line_copy = dict(line)
            line_copy["translation"] = translated_text
            line_copy["status"] = "ready"
            translated_lines.append(line_copy)

        logger.info(f"[TRANSLATION] Translation completed for all {len(lines)} lines.")
        return translated_lines

    async def translate_single_line(
        self,
        original: str,
        source_lang: str,
        target_lang: str,
        duration: Optional[float] = None,
        speaker_info: Optional[str] = None
    ) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.provider.translate_dialogue,
            original,
            source_lang,
            target_lang,
            None,
            None,
            speaker_info,
            duration
        )

translation_service = TranslationService()
