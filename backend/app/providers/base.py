from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ASRSegment:
    def __init__(self, start: float, end: float, text: str, confidence: float = 0.95, speaker: Optional[str] = None):
        self.start = start
        self.end = end
        self.text = text
        self.confidence = confidence
        self.speaker = speaker

    def to_dict(self) -> Dict[str, Any]:
        return {
            "speaker": self.speaker,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "text": self.text,
            "confidence": round(self.confidence, 2)
        }

class ASRProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> List[ASRSegment]:
        pass

class LLMTranslationProvider(ABC):
    @abstractmethod
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
        pass

class TTSProvider(ABC):
    @abstractmethod
    async def generate_voice(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> str:
        pass

    @abstractmethod
    async def generate_preview(self, voice_id: str, output_path: str, sample_text: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def get_available_voices(self, language: str) -> List[Dict[str, Any]]:
        pass
