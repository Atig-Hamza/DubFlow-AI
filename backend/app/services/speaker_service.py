import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.app.core.config import VOICES_DIR
from backend.app.core.logging import logger
from backend.app.services.language_service import language_manager
from backend.app.utils.audio import analyze_vocal_characteristics
from backend.app.utils.ffmpeg import run_ffmpeg

class SpeakerService:
    """
    Manages speaker profiles, voice characteristics (pitch, speed, loudness),
    representative audio sample extraction, and neural voice assignments.
    """
    def __init__(self):
        pass

    async def create_speaker_profiles(
        self,
        project_id: str,
        target_language: str,
        aligned_lines: List[Dict[str, Any]],
        audio_path: str
    ) -> List[Dict[str, Any]]:
        """
        Creates detailed speaker profiles with acoustic metrics and voice previews.
        """
        # Group lines by speaker
        speakers_map: Dict[str, List[Dict[str, Any]]] = {}
        for line in aligned_lines:
            spk = line["speaker"]
            if spk not in speakers_map:
                speakers_map[spk] = []
            speakers_map[spk].append(line)

        speaker_profiles: List[Dict[str, Any]] = []

        for idx, (spk_tag, lines) in enumerate(sorted(speakers_map.items())):
            # 1. Compute aggregate statistics
            total_duration = sum(line["end"] - line["start"] for line in lines)
            segments_count = len(lines)

            # 2. Pick the cleanest/longest segment for vocal characterization & preview sample
            best_line = max(lines, key=lambda l: (l["end"] - l["start"]))
            best_start = best_line["start"]
            best_end = min(best_start + 4.5, best_line["end"])  # up to 4.5 seconds for preview clip

            # 3. Analyze vocal characteristics
            characteristics = analyze_vocal_characteristics(audio_path, best_start, best_end)

            # 4. Extract clean sample audio clip for frontend preview
            preview_filename = f"{project_id}_{spk_tag}_sample.wav"
            preview_path = str(VOICES_DIR / preview_filename)
            try:
                await run_ffmpeg([
                    "-ss", str(best_start),
                    "-to", str(best_end),
                    "-i", audio_path,
                    "-ar", "24000",
                    "-ac", "1",
                    preview_path
                ])
            except Exception as e:
                logger.warning(f"[SPEAKER] Failed to extract sample clip for {spk_tag}: {e}")
                preview_path = ""

            # 5. Automatically assign best matching neural voice from target language
            assigned_voice = language_manager.get_voice_for_speaker(
                target_lang=target_language,
                gender=characteristics["gender_detected"],
                speaker_index=idx
            )

            # Speaker default display name
            spk_number = spk_tag.replace("speaker_", "")
            display_name = f"Speaker {spk_number}"

            speaker_profiles.append({
                "speaker_tag": spk_tag,
                "display_name": display_name,
                "segments_count": segments_count,
                "total_speech_time": round(total_duration, 2),
                "avg_pitch": characteristics["avg_pitch"],
                "speaking_rate": characteristics["speaking_rate"],
                "loudness": characteristics["loudness"],
                "gender_detected": characteristics["gender_detected"],
                "confidence": characteristics["confidence"],
                "sample_audio_path": preview_path,
                "assigned_voice_id": assigned_voice,
                "voice_consent": True
            })

        logger.info(f"[SPEAKER] Created {len(speaker_profiles)} speaker profile(s).")
        return speaker_profiles

speaker_service = SpeakerService()
