import re
from typing import Optional
from openai import OpenAI
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.providers.base import LLMTranslationProvider

class NVIDIALLMProvider(LLMTranslationProvider):
    """
    NVIDIA-hosted AI Translation & Dialogue Adaptation Provider.
    Uses NVIDIA Integrate APIs (such as nvidia/riva-translate-4b-instruct-v2).
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.model = model or settings.NVIDIA_TRANSLATION_MODEL
        self.base_url = settings.NVIDIA_BASE_URL
        self._client = None

    def _get_client(self) -> OpenAI:
        if not self.api_key or self.api_key == "your_nvidia_api_key_here":
            raise ValueError("NVIDIA API key not configured in .env")
        if self._client is None:
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=25.0
            )
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("nvapi-"))

    def translate_dialogue(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        previous_context: Optional[str] = None,
        next_context: Optional[str] = None,
        speaker_info: Optional[str] = None,
        target_duration: Optional[float] = None
    ) -> str:
        if not text or not text.strip():
            return ""

        if not self.is_configured():
            logger.warning("[TRANSLATION] NVIDIA API key not configured, using fallback.")
            return text

        client = self._get_client()
        
        # Build contextual instructions for video dubbing
        duration_desc = f"~{target_duration:.1f} seconds" if target_duration else "brief spoken time"
        sys_prompt = (
            f"You are an expert audiovisual dubbing translator. Translate the dialogue line from {source_lang} to natural {target_lang}.\n"
            f"CRITICAL DUBBING CONSTRAINTS:\n"
            f"1. Spoken Duration: The line must comfortably fit in {duration_desc}. Be concise, punchy, and natural. Avoid wordiness or filler.\n"
            f"2. Meaning & Emotion: Preserve conversational intent and emotional tone.\n"
            f"3. Output: Return ONLY the translated spoken dialogue without quotes, brackets, or explanations."
        )

        user_content = f"Line to dub: \"{text.strip()}\""
        if previous_context:
            user_content += f" (Context before: \"{previous_context.strip()}\")"

        # Try Llama 3.2 instruction translation first for duration adaptation
        primary_model = "meta/llama-3.2-11b-vision-instruct"
        fallback_model = self.model or "nvidia/riva-translate-4b-instruct-v2"

        try:
            response = client.chat.completions.create(
                model=primary_model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=100,
                temperature=0.2,
                timeout=12.0
            )
            raw_result = response.choices[0].message.content.strip()
            cleaned = re.sub(r'^(Translation|Traduction|Traducción|Übersetzung|الترجمة)\s*:\s*', '', raw_result, flags=re.IGNORECASE)
            cleaned = cleaned.strip('"\'')
            logger.info(f"[TRANSLATION] [Model: {primary_model}] '{text}' -> '{cleaned}'")
            return cleaned
        except Exception as e1:
            logger.warning(f"[TRANSLATION] Primary model ({primary_model}) unavailable or timed out: {e1}. Using Riva fallback...")
            try:
                # Riva fallback prompt
                riva_prompt = f"Translate {source_lang} to {target_lang}: {text.strip()}"
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=[
                        {"role": "user", "content": riva_prompt}
                    ],
                    max_tokens=150,
                    temperature=0.2,
                    timeout=15.0
                )
                raw_result = response.choices[0].message.content.strip()
                cleaned = re.sub(r'^(Translation|Traduction|Traducción|Übersetzung|الترجمة)\s*:\s*', '', raw_result, flags=re.IGNORECASE)
                cleaned = cleaned.strip('"\'')
                logger.info(f"[TRANSLATION] [Fallback: {fallback_model}] '{text}' -> '{cleaned}'")
                return cleaned
            except Exception as e2:
                logger.error(f"[TRANSLATION] Both translation models failed: {e2}")
                return text
