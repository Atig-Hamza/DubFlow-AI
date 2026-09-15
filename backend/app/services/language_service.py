import re
import asyncio
from typing import Dict, List, Optional, Any
import edge_tts
from backend.app.core.logging import logger

class LanguageMetadata:
    def __init__(self, code: str, name: str, native_name: str, flag: str, voices: List[Dict[str, Any]]):
        self.code = code
        self.name = name
        self.native_name = native_name
        self.flag = flag
        self.voices = voices

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "native_name": self.native_name,
            "flag": self.flag,
            "voices": self.voices,
        }

class LanguageManager:
    """
    Manages 320+ studio-grade neural voices with deep specialist catalogs
    for Arabic (32+ regional dialect voices), English, French, Spanish, German, etc.
    Supports filtering by Gender, Country/Dialect, and Search query.
    """
    def __init__(self):
        self._all_voices_cache: List[Dict[str, Any]] = []
        self._initialized = False
        self.languages: Dict[str, LanguageMetadata] = self._build_base_catalog()

    def _build_base_catalog(self) -> Dict[str, LanguageMetadata]:
        # Curated foundational catalog
        arabic_voices = [
            {"id": "ar-EG-SalmaNeural", "name": "Salma (Egyptian, Friendly Studio)", "gender": "Female", "country": "Egypt", "dialect": "Egyptian", "flag": "🇪🇬", "style": "Friendly"},
            {"id": "ar-EG-ShakirNeural", "name": "Shakir (Egyptian, Authoritative)", "gender": "Male", "country": "Egypt", "dialect": "Egyptian", "flag": "🇪🇬", "style": "Resonant"},
            {"id": "ar-SA-HamedNeural", "name": "Hamed (Saudi, Formal Resonant)", "gender": "Male", "country": "Saudi Arabia", "dialect": "Gulf", "flag": "🇸🇦", "style": "Authoritative"},
            {"id": "ar-SA-ZariyahNeural", "name": "Zariyah (Saudi, Eloquent & Warm)", "gender": "Female", "country": "Saudi Arabia", "dialect": "Gulf", "flag": "🇸🇦", "style": "Graceful"},
            {"id": "ar-AE-HamdanNeural", "name": "Hamdan (Emirati, Modern Gulf)", "gender": "Male", "country": "UAE", "dialect": "Emirati", "flag": "🇦🇪", "style": "Polite"},
            {"id": "ar-AE-FatimaNeural", "name": "Fatima (Emirati, Melodic & Soft)", "gender": "Female", "country": "UAE", "dialect": "Emirati", "flag": "🇦🇪", "style": "Soft"},
            {"id": "ar-MA-JamalNeural", "name": "Jamal (Moroccan, Darija & Modern)", "gender": "Male", "country": "Morocco", "dialect": "Maghrebi", "flag": "🇲🇦", "style": "Warm"},
            {"id": "ar-MA-MounaNeural", "name": "Mouna (Moroccan, Expressive)", "gender": "Female", "country": "Morocco", "dialect": "Maghrebi", "flag": "🇲🇦", "style": "Expressive"},
            {"id": "ar-DZ-IsmaelNeural", "name": "Ismael (Algerian, Dynamic)", "gender": "Male", "country": "Algeria", "dialect": "Maghrebi", "flag": "🇩🇿", "style": "Dynamic"},
            {"id": "ar-DZ-AminaNeural", "name": "Amina (Algerian, Clear Voice)", "gender": "Female", "country": "Algeria", "dialect": "Maghrebi", "flag": "🇩🇿", "style": "Clear"},
            {"id": "ar-TN-HediNeural", "name": "Hedi (Tunisian, Natural Pacing)", "gender": "Male", "country": "Tunisia", "dialect": "Maghrebi", "flag": "🇹🇳", "style": "Natural"},
            {"id": "ar-TN-ReemNeural", "name": "Reem (Tunisian, Gentle Eloquence)", "gender": "Female", "country": "Tunisia", "dialect": "Maghrebi", "flag": "🇹🇳", "style": "Gentle"},
            {"id": "ar-IQ-BasselNeural", "name": "Bassel (Iraqi, Deep Voiceover)", "gender": "Male", "country": "Iraq", "dialect": "Mesopotamian", "flag": "🇮🇶", "style": "Deep"},
            {"id": "ar-IQ-RanaNeural", "name": "Rana (Iraqi, Expressive)", "gender": "Female", "country": "Iraq", "dialect": "Mesopotamian", "flag": "🇮🇶", "style": "Expressive"},
            {"id": "ar-JO-TaimNeural", "name": "Taim (Jordanian, Modern Levantine)", "gender": "Male", "country": "Jordan", "dialect": "Levantine", "flag": "🇯🇴", "style": "Conversational"},
            {"id": "ar-JO-SanaNeural", "name": "Sana (Jordanian, Engaging)", "gender": "Female", "country": "Jordan", "dialect": "Levantine", "flag": "🇯🇴", "style": "Engaging"},
            {"id": "ar-LB-RamiNeural", "name": "Rami (Lebanese, Smooth & Warm)", "gender": "Male", "country": "Lebanon", "dialect": "Levantine", "flag": "🇱🇧", "style": "Smooth"},
            {"id": "ar-LB-LaylaNeural", "name": "Layla (Lebanese, Melodic)", "gender": "Female", "country": "Lebanon", "dialect": "Levantine", "flag": "🇱🇧", "style": "Melodic"},
            {"id": "ar-KW-FahedNeural", "name": "Fahed (Kuwaiti, Clear & Formal)", "gender": "Male", "country": "Kuwait", "dialect": "Gulf", "flag": "🇰🇼", "style": "Formal"},
            {"id": "ar-KW-NouraNeural", "name": "Noura (Kuwaiti, Graceful)", "gender": "Female", "country": "Kuwait", "dialect": "Gulf", "flag": "🇰🇼", "style": "Graceful"},
            {"id": "ar-QA-MoazNeural", "name": "Moaz (Qatari, Professional)", "gender": "Male", "country": "Qatar", "dialect": "Gulf", "flag": "🇶🇦", "style": "Professional"},
            {"id": "ar-QA-AmalNeural", "name": "Amal (Qatari, Confident)", "gender": "Female", "country": "Qatar", "dialect": "Gulf", "flag": "🇶🇦", "style": "Confident"},
            {"id": "ar-OM-AbdullahNeural", "name": "Abdullah (Omani, Classic)", "gender": "Male", "country": "Oman", "dialect": "Gulf", "flag": "🇴🇲", "style": "Classic"},
            {"id": "ar-OM-AyshaNeural", "name": "Aysha (Omani, Soft)", "gender": "Female", "country": "Oman", "dialect": "Gulf", "flag": "🇴🇲", "style": "Soft"},
            {"id": "ar-SY-LaithNeural", "name": "Laith (Syrian, Deep & Articulate)", "gender": "Male", "country": "Syria", "dialect": "Levantine", "flag": "🇸🇾", "style": "Articulate"},
            {"id": "ar-SY-AmanyNeural", "name": "Amany (Syrian, Pleasant)", "gender": "Female", "country": "Syria", "dialect": "Levantine", "flag": "🇸🇾", "style": "Pleasant"},
            {"id": "ar-YE-SalehNeural", "name": "Saleh (Yemeni, Traditional)", "gender": "Male", "country": "Yemen", "dialect": "Yemeni", "flag": "🇾🇪", "style": "Traditional"},
            {"id": "ar-YE-MaryamNeural", "name": "Maryam (Yemeni, Eloquent)", "gender": "Female", "country": "Yemen", "dialect": "Yemeni", "flag": "🇾🇪", "style": "Eloquent"},
            {"id": "ar-LY-OmarNeural", "name": "Omar (Libyan, Direct & Crisp)", "gender": "Male", "country": "Libya", "dialect": "Maghrebi", "flag": "🇱🇾", "style": "Direct"},
            {"id": "ar-LY-ImanNeural", "name": "Iman (Libyan, Clear & Warm)", "gender": "Female", "country": "Libya", "dialect": "Maghrebi", "flag": "🇱🇾", "style": "Warm"},
            {"id": "ar-BH-AliNeural", "name": "Ali (Bahraini, Expressive)", "gender": "Male", "country": "Bahrain", "dialect": "Gulf", "flag": "🇧🇭", "style": "Expressive"},
            {"id": "ar-BH-LailaNeural", "name": "Laila (Bahraini, Natural)", "gender": "Female", "country": "Bahrain", "dialect": "Gulf", "flag": "🇧🇭", "style": "Natural"},
            # Multilingual studio models that also support Arabic
            {"id": "en-US-AndrewMultilingualNeural", "name": "Andrew (Multilingual Studio Master)", "gender": "Male", "country": "Global", "dialect": "Multilingual", "flag": "🌐", "style": "Cinematic"},
            {"id": "en-US-AvaMultilingualNeural", "name": "Ava (Multilingual Engaging)", "gender": "Female", "country": "Global", "dialect": "Multilingual", "flag": "🌐", "style": "Conversational"},
            {"id": "fr-FR-VivienneMultilingualNeural", "name": "Vivienne (Multilingual Studio Voice)", "gender": "Female", "country": "Global", "dialect": "Multilingual", "flag": "🌐", "style": "Expressive"},
            {"id": "fr-FR-RemyMultilingualNeural", "name": "Remy (Multilingual Voiceover)", "gender": "Male", "country": "Global", "dialect": "Multilingual", "flag": "🌐", "style": "Broadcast"}
        ]

        english_voices = [
            {"id": "en-US-AndrewMultilingualNeural", "name": "Andrew (US, Expressive Studio)", "gender": "Male", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Studio Master"},
            {"id": "en-US-AvaMultilingualNeural", "name": "Ava (US, Natural & Engaging)", "gender": "Female", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Conversational"},
            {"id": "en-US-BrianMultilingualNeural", "name": "Brian (US, Deep Professional)", "gender": "Male", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Deep"},
            {"id": "en-US-EmmaMultilingualNeural", "name": "Emma (US, Warm & Friendly)", "gender": "Female", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Warm"},
            {"id": "en-US-GuyNeural", "name": "Guy (US, News & Narration)", "gender": "Male", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Broadcast"},
            {"id": "en-US-JennyNeural", "name": "Jenny (US, Versatile & Melodic)", "gender": "Female", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Versatile"},
            {"id": "en-US-AriaNeural", "name": "Aria (US, Cinematic Voiceover)", "gender": "Female", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Cinematic"},
            {"id": "en-US-ChristopherNeural", "name": "Christopher (US, Structured & Crisp)", "gender": "Male", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Crisp"},
            {"id": "en-US-EricNeural", "name": "Eric (US, Friendly Commercial)", "gender": "Male", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Friendly"},
            {"id": "en-US-MichelleNeural", "name": "Michelle (US, Soft & Natural)", "gender": "Female", "country": "USA", "dialect": "American", "flag": "🇺🇸", "style": "Soft"},
            {"id": "en-GB-RyanNeural", "name": "Ryan (British, BBC Broadcast)", "gender": "Male", "country": "UK", "dialect": "British", "flag": "🇬🇧", "style": "Broadcast"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia (British, Elegant & Clear)", "gender": "Female", "country": "UK", "dialect": "British", "flag": "🇬🇧", "style": "Elegant"},
            {"id": "en-GB-LibbyNeural", "name": "Libby (British, Warm Storyteller)", "gender": "Female", "country": "UK", "dialect": "British", "flag": "🇬🇧", "style": "Storyteller"},
            {"id": "en-GB-ThomasNeural", "name": "Thomas (British, Deep & Classic)", "gender": "Male", "country": "UK", "dialect": "British", "flag": "🇬🇧", "style": "Classic"},
            {"id": "en-AU-WilliamNeural", "name": "William (Australian, Confident)", "gender": "Male", "country": "Australia", "dialect": "Australian", "flag": "🇦🇺", "style": "Confident"},
            {"id": "en-AU-NatashaNeural", "name": "Natasha (Australian, Bright & Natural)", "gender": "Female", "country": "Australia", "dialect": "Australian", "flag": "🇦🇺", "style": "Bright"},
            {"id": "en-CA-LiamNeural", "name": "Liam (Canadian, Modern Narration)", "gender": "Male", "country": "Canada", "dialect": "Canadian", "flag": "🇨🇦", "style": "Modern"},
            {"id": "en-CA-ClaraNeural", "name": "Clara (Canadian, Gentle & Clear)", "gender": "Female", "country": "Canada", "dialect": "Canadian", "flag": "🇨🇦", "style": "Gentle"},
            {"id": "en-IE-ConnorNeural", "name": "Connor (Irish, Charming & Melodic)", "gender": "Male", "country": "Ireland", "dialect": "Irish", "flag": "🇮🇪", "style": "Melodic"},
            {"id": "en-IE-EmilyNeural", "name": "Emily (Irish, Friendly)", "gender": "Female", "country": "Ireland", "dialect": "Irish", "flag": "🇮🇪", "style": "Friendly"}
        ]

        french_voices = [
            {"id": "fr-FR-VivienneMultilingualNeural", "name": "Vivienne (French, Studio Master)", "gender": "Female", "country": "France", "dialect": "Metropolitan", "flag": "🇫🇷", "style": "Studio Master"},
            {"id": "fr-FR-RemyMultilingualNeural", "name": "Remy (French, Cinematic Voiceover)", "gender": "Male", "country": "France", "dialect": "Metropolitan", "flag": "🇫🇷", "style": "Cinematic"},
            {"id": "fr-FR-HenriNeural", "name": "Henri (French, Deep & Articulate)", "gender": "Male", "country": "France", "dialect": "Metropolitan", "flag": "🇫🇷", "style": "Deep"},
            {"id": "fr-FR-DeniseNeural", "name": "Denise (French, Warm & Natural)", "gender": "Female", "country": "France", "dialect": "Metropolitan", "flag": "🇫🇷", "style": "Warm"},
            {"id": "fr-FR-EloiseNeural", "name": "Eloise (French, Youthful & Dynamic)", "gender": "Female", "country": "France", "dialect": "Metropolitan", "flag": "🇫🇷", "style": "Dynamic"},
            {"id": "fr-FR-AlainNeural", "name": "Alain (French, Authoritative)", "gender": "Male", "country": "France", "dialect": "Metropolitan", "flag": "🇫🇷", "style": "Authoritative"},
            {"id": "fr-CA-AntoineNeural", "name": "Antoine (Quebec, Modern Canadian)", "gender": "Male", "country": "Canada", "dialect": "Quebecois", "flag": "🇨🇦", "style": "Modern"},
            {"id": "fr-CA-SylvieNeural", "name": "Sylvie (Quebec, Warm & Clear)", "gender": "Female", "country": "Canada", "dialect": "Quebecois", "flag": "🇨🇦", "style": "Warm"},
            {"id": "fr-BE-GerardNeural", "name": "Gerard (Belgian, Classic)", "gender": "Male", "country": "Belgium", "dialect": "Belgian", "flag": "🇧🇪", "style": "Classic"},
            {"id": "fr-CH-FabriceNeural", "name": "Fabrice (Swiss, Structured)", "gender": "Male", "country": "Switzerland", "dialect": "Swiss", "flag": "🇨🇭", "style": "Structured"}
        ]

        spanish_voices = [
            {"id": "es-ES-AlvaroNeural", "name": "Alvaro (Castilian, Studio Confident)", "gender": "Male", "country": "Spain", "dialect": "Castilian", "flag": "🇪🇸", "style": "Confident"},
            {"id": "es-ES-ElviraNeural", "name": "Elvira (Castilian, Expressive Melodic)", "gender": "Female", "country": "Spain", "dialect": "Castilian", "flag": "🇪🇸", "style": "Expressive"},
            {"id": "es-MX-DaliaNeural", "name": "Dalia (Mexican, Smooth Modern Latin)", "gender": "Female", "country": "Mexico", "dialect": "Mexican", "flag": "🇲🇽", "style": "Smooth"},
            {"id": "es-MX-JorgeNeural", "name": "Jorge (Mexican, Dynamic Narration)", "gender": "Male", "country": "Mexico", "dialect": "Mexican", "flag": "🇲🇽", "style": "Dynamic"},
            {"id": "es-AR-TomasNeural", "name": "Tomas (Argentine, Rioplatense)", "gender": "Male", "country": "Argentina", "dialect": "Argentine", "flag": "🇦🇷", "style": "Natural"},
            {"id": "es-AR-ElenaNeural", "name": "Elena (Argentine, Expressive)", "gender": "Female", "country": "Argentina", "dialect": "Argentine", "flag": "🇦🇷", "style": "Expressive"},
            {"id": "es-CO-GonzaloNeural", "name": "Gonzalo (Colombian, Crisp Voice)", "gender": "Male", "country": "Colombia", "dialect": "Colombian", "flag": "🇨🇴", "style": "Crisp"},
            {"id": "es-CO-SalomeNeural", "name": "Salome (Colombian, Pleasant)", "gender": "Female", "country": "Colombia", "dialect": "Colombian", "flag": "🇨🇴", "style": "Pleasant"}
        ]

        german_voices = [
            {"id": "de-DE-FlorianMultilingualNeural", "name": "Florian (German, Studio Voiceover)", "gender": "Male", "country": "Germany", "dialect": "Standard", "flag": "🇩🇪", "style": "Studio Master"},
            {"id": "de-DE-SeraphinaMultilingualNeural", "name": "Seraphina (German, Expressive & Clear)", "gender": "Female", "country": "Germany", "dialect": "Standard", "flag": "🇩🇪", "style": "Expressive"},
            {"id": "de-DE-ConradNeural", "name": "Conrad (German, Deep & Structured)", "gender": "Male", "country": "Germany", "dialect": "Standard", "flag": "🇩🇪", "style": "Deep"},
            {"id": "de-DE-KatjaNeural", "name": "Katja (German, Pleasant & Natural)", "gender": "Female", "country": "Germany", "dialect": "Standard", "flag": "🇩🇪", "style": "Natural"},
            {"id": "de-AT-JonasNeural", "name": "Jonas (Austrian, Smooth)", "gender": "Male", "country": "Austria", "dialect": "Austrian", "flag": "🇦🇹", "style": "Smooth"}
        ]

        turkish_voices = [
            {"id": "tr-TR-AhmetNeural", "name": "Ahmet (Turkish, Resonant & Clean)", "gender": "Male", "country": "Turkey", "dialect": "Standard", "flag": "🇹🇷", "style": "Resonant"},
            {"id": "tr-TR-EmelNeural", "name": "Emel (Turkish, Lively & Expressive)", "gender": "Female", "country": "Turkey", "dialect": "Standard", "flag": "🇹🇷", "style": "Lively"}
        ]

        portuguese_voices = [
            {"id": "pt-BR-ThalitaMultilingualNeural", "name": "Thalita (Brazilian, Studio Mastered)", "gender": "Female", "country": "Brazil", "dialect": "Brazilian", "flag": "🇧🇷", "style": "Studio Master"},
            {"id": "pt-BR-AntonioNeural", "name": "Antonio (Brazilian, Expressive & Warm)", "gender": "Male", "country": "Brazil", "dialect": "Brazilian", "flag": "🇧🇷", "style": "Warm"},
            {"id": "pt-PT-DuarteNeural", "name": "Duarte (European Portuguese, Classic)", "gender": "Male", "country": "Portugal", "dialect": "European", "flag": "🇵🇹", "style": "Classic"}
        ]

        italian_voices = [
            {"id": "it-IT-GiuseppeMultilingualNeural", "name": "Giuseppe (Italian, Studio Cinema)", "gender": "Male", "country": "Italy", "dialect": "Standard", "flag": "🇮🇹", "style": "Cinematic"},
            {"id": "it-IT-ElsaNeural", "name": "Elsa (Italian, Vibrant & Melodic)", "gender": "Female", "country": "Italy", "dialect": "Standard", "flag": "🇮🇹", "style": "Vibrant"},
            {"id": "it-IT-DiegoNeural", "name": "Diego (Italian, Warm & Natural)", "gender": "Male", "country": "Italy", "dialect": "Standard", "flag": "🇮🇹", "style": "Warm"}
        ]

        return {
            "Arabic": LanguageMetadata(code="ar", name="Arabic", native_name="العربية", flag="🇸🇦", voices=arabic_voices),
            "English": LanguageMetadata(code="en", name="English", native_name="English", flag="🇺🇸", voices=english_voices),
            "French": LanguageMetadata(code="fr", name="French", native_name="Français", flag="🇫🇷", voices=french_voices),
            "Spanish": LanguageMetadata(code="es", name="Spanish", native_name="Español", flag="🇪🇸", voices=spanish_voices),
            "German": LanguageMetadata(code="de", name="German", native_name="Deutsch", flag="🇩🇪", voices=german_voices),
            "Turkish": LanguageMetadata(code="tr", name="Turkish", native_name="Türkçe", flag="🇹🇷", voices=turkish_voices),
            "Portuguese": LanguageMetadata(code="pt", name="Portuguese", native_name="Português", flag="🇧🇷", voices=portuguese_voices),
            "Italian": LanguageMetadata(code="it", name="Italian", native_name="Italiano", flag="🇮🇹", voices=italian_voices),
        }

    async def initialize_all_voices(self):
        """
        Dynamically discovers and indexes all 320+ voices from Edge-TTS.
        """
        if self._initialized:
            return
        try:
            raw_voices = await edge_tts.list_voices()
            parsed: List[Dict[str, Any]] = []
            for v in raw_voices:
                short = v["ShortName"]
                locale = v.get("Locale", "")
                locale_name = v.get("LocaleName", "")
                gender = v.get("Gender", "Unknown")

                # Parse country/dialect from LocaleName, e.g. "Arabic (Egypt)"
                country = locale_name
                if "(" in locale_name and ")" in locale_name:
                    country = locale_name.split("(")[1].split(")")[0].strip()

                flag = "🌐"
                if locale.startswith("ar-"):
                    flag = "🇸🇦" if "SA" in locale else ("🇪🇬" if "EG" in locale else ("🇦🇪" if "AE" in locale else ("🇲🇦" if "MA" in locale else "🌍")))
                elif locale.startswith("en-"):
                    flag = "🇺🇸" if "US" in locale else ("🇬🇧" if "GB" in locale else ("🇦🇺" if "AU" in locale else "🇨🇦"))
                elif locale.startswith("fr-"):
                    flag = "🇫🇷" if "FR" in locale else "🇨🇦"
                elif locale.startswith("es-"):
                    flag = "🇪🇸" if "ES" in locale else "🇲🇽"
                elif locale.startswith("de-"):
                    flag = "🇩🇪"
                elif locale.startswith("it-"):
                    flag = "🇮🇹"
                elif locale.startswith("tr-"):
                    flag = "🇹🇷"
                elif locale.startswith("pt-"):
                    flag = "🇧🇷" if "BR" in locale else "🇵🇹"

                # Extract friendly short name
                clean_name = short.split("-")[-1].replace("Neural", "")
                if "Multilingual" in clean_name:
                    clean_name = clean_name.replace("Multilingual", " (Multilingual)")

                parsed.append({
                    "id": short,
                    "name": f"{clean_name} - {country}",
                    "short_name": short,
                    "gender": gender,
                    "locale": locale,
                    "country": country,
                    "dialect": country,
                    "flag": flag,
                    "style": "Studio Neural",
                    "is_multilingual": "Multilingual" in short
                })

            self._all_voices_cache = parsed
            self._initialized = True
            logger.info(f"[LANG] Indexed {len(parsed)} studio neural voices from Edge-TTS.")
        except Exception as e:
            logger.warning(f"[LANG] Failed to fetch dynamic voice list from Edge-TTS: {e}")

    def filter_voices(
        self,
        language: Optional[str] = None,
        gender: Optional[str] = None,
        dialect: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filters voices by language (e.g. 'Arabic', 'ar'), gender ('Male', 'Female'), dialect/country, and search query.
        Returns up to 80+ matching voices.
        """
        # Determine language code filter
        lang_code = ""
        if language:
            target = language.strip().lower()
            for name, meta in self.languages.items():
                if name.lower() == target or meta.code.lower() == target:
                    lang_code = meta.code
                    break
            if not lang_code:
                lang_code = target[:2]

        # Use curated language voices or full cache
        candidates: List[Dict[str, Any]] = []
        if self._all_voices_cache:
            candidates = list(self._all_voices_cache)
        else:
            # Fallback to local catalog
            for meta in self.languages.values():
                for v in meta.voices:
                    candidates.append({
                        "id": v["id"],
                        "name": v["name"],
                        "short_name": v["id"],
                        "gender": v.get("gender", "Unknown"),
                        "locale": meta.code,
                        "country": v.get("country", meta.name),
                        "dialect": v.get("dialect", "Standard"),
                        "flag": v.get("flag", meta.flag),
                        "style": v.get("style", "Studio"),
                        "is_multilingual": "Multilingual" in v["id"]
                    })

        results = []
        for v in candidates:
            # Language match
            if lang_code:
                # Direct locale prefix or multilingual support
                if not (v["locale"].lower().startswith(lang_code.lower()) or v.get("is_multilingual")):
                    continue

            # Gender filter
            if gender and gender.lower() != "all":
                if v["gender"].lower() != gender.lower():
                    continue

            # Dialect / Country filter
            if dialect and dialect.lower() != "all":
                if dialect.lower() not in v.get("country", "").lower() and dialect.lower() not in v.get("dialect", "").lower():
                    continue

            # Search query filter
            if search and search.strip():
                q = search.strip().lower()
                text_corpus = f"{v['id']} {v['name']} {v.get('country', '')} {v.get('dialect', '')} {v.get('style', '')}".lower()
                if q not in text_corpus:
                    continue

            results.append(v)

        return results

    def get_supported_languages(self) -> List[Dict[str, Any]]:
        return [lang.to_dict() for lang in self.languages.values()]

    def get_language(self, name_or_code: str) -> Optional[LanguageMetadata]:
        target = name_or_code.strip().lower()
        for name, meta in self.languages.items():
            if name.lower() == target or meta.code.lower() == target:
                return meta
        return self.languages.get("Arabic") or self.languages.get("French")

    def get_voice_for_speaker(self, target_lang: str, gender: str = "Unknown", speaker_index: int = 0) -> str:
        meta = self.get_language(target_lang)
        if not meta or not meta.voices:
            return "ar-SA-HamedNeural"
        
        gender_matches = [v for v in meta.voices if v.get("gender", "").lower() == gender.lower()]
        if gender_matches:
            return gender_matches[speaker_index % len(gender_matches)]["id"]
        
        return meta.voices[speaker_index % len(meta.voices)]["id"]

language_manager = LanguageManager()
