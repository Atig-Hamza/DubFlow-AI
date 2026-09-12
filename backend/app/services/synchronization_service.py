import os
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.core.config import SEGMENTS_DIR
from backend.app.core.logging import logger
from backend.app.utils.audio import get_audio_duration
from backend.app.utils.ffmpeg import run_ffmpeg

class SynchronizationService:
    """
    Synchronizes generated dialogue speech with the original video timestamp windows.
    Applies audio time stretching (atempo), padding, and duration matching.
    """
    def __init__(self):
        pass

    async def synchronize_line_audio(
        self,
        raw_audio_path: str,
        project_id: str,
        line_id: str,
        target_start: float,
        target_end: float,
        next_start: Optional[float] = None,
        max_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Adjusts generated audio to fit within target window using FFmpeg atempo filter.
        """
        if not os.path.exists(raw_audio_path):
            raise FileNotFoundError(f"Raw audio segment not found: {raw_audio_path}")

        target_duration = max(0.4, target_end - target_start)
        actual_duration = get_audio_duration(raw_audio_path)

        synced_filename = f"{project_id}_{line_id}_synced.wav"
        synced_path = str(SEGMENTS_DIR / synced_filename)

        if actual_duration <= 0.05:
            return {"synced_path": raw_audio_path, "ratio": 1.0, "final_duration": target_duration}

        tempo_ratio = actual_duration / target_duration
        clamped_ratio = max(0.5, min(2.0, tempo_ratio))

        cmd = [
            "ffmpeg", "-y", "-i", raw_audio_path,
            "-filter:a", f"atempo={clamped_ratio:.4f}",
            "-ar", "24000", "-ac", "1", synced_path
        ]
        await run_ffmpeg(cmd)
        return {
            "synced_path": synced_path,
            "ratio": clamped_ratio,
            "final_duration": get_audio_duration(synced_path)
        }
