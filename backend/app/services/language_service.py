from typing import List, Dict, Any

class LanguageService:
    """
    International language and neural voice catalog service.
    """
    SUPPORTED_LANGUAGES = [
        {"code": "en", "name": "English", "flag": "🇺🇸"},
        {"code": "ar", "name": "Arabic", "flag": "🇸🇦"},
        {"code": "es", "name": "Spanish", "flag": "🇪🇸"},
        {"code": "fr", "name": "French", "flag": "🇫🇷"},
        {"code": "de", "name": "German", "flag": "🇩🇪"},
        {"code": "it", "name": "Italian", "flag": "🇮🇹"},
        {"code": "ja", "name": "Japanese", "flag": "🇯🇵"},
        {"code": "ko", "name": "Korean", "flag": "🇰🇷"},
        {"code": "zh", "name": "Chinese", "flag": "🇨🇳"},
        {"code": "pt", "name": "Portuguese", "flag": "🇧🇷"},
        {"code": "ru", "name": "Russian", "flag": "🇷🇺"},
        {"code": "tr", "name": "Turkish", "flag": "🇹🇷"},
        {"code": "hi", "name": "Hindi", "flag": "🇮🇳"}
    ]

    VOICES_CATALOG = [
        {"id": "en-US-GuyNeural", "name": "Guy", "gender": "male", "lang": "en", "provider": "edge", "locale": "en-US", "country": "United States", "dialect": "General American"},
        {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "female", "lang": "en", "provider": "edge", "locale": "en-US", "country": "United States", "dialect": "General American"},
        {"id": "ar-SA-HamedNeural", "name": "Hamed", "gender": "male", "lang": "ar", "provider": "edge", "locale": "ar-SA", "country": "Saudi Arabia", "dialect": "Gulf / Standard"},
        {"id": "ar-SA-ZariyahNeural", "name": "Zariyah", "gender": "female", "lang": "ar", "provider": "edge", "locale": "ar-SA", "country": "Saudi Arabia", "dialect": "Gulf / Standard"},
        {"id": "es-ES-AlvaroNeural", "name": "Alvaro", "gender": "male", "lang": "es", "provider": "edge", "locale": "es-ES", "country": "Spain", "dialect": "Castilian"},
        {"id": "fr-FR-HenriNeural", "name": "Henri", "gender": "male", "lang": "fr", "provider": "edge", "locale": "fr-FR", "country": "France", "dialect": "Parisian"},
        {"id": "de-DE-ConradNeural", "name": "Conrad", "gender": "male", "lang": "de", "provider": "edge", "locale": "de-DE", "country": "Germany", "dialect": "Standard German"}
    ]

    @classmethod
    def get_supported_languages(cls) -> List[Dict[str, Any]]:
        return cls.SUPPORTED_LANGUAGES

    @classmethod
    def get_available_voices(cls, lang: str = None, gender: str = None) -> List[Dict[str, Any]]:
        voices = cls.VOICES_CATALOG
        if lang:
            voices = [v for v in voices if v["lang"] == lang]
        if gender:
            voices = [v for v in voices if v["gender"] == gender]
        return voices

    @classmethod
    def get_default_voice_for_speaker(cls, lang: str, gender: str = "male", speaker_idx: int = 0) -> str:
        matching = cls.get_available_voices(lang=lang, gender=gender)
        if matching:
            return matching[speaker_idx % len(matching)]["id"]
        return "en-US-GuyNeural"
