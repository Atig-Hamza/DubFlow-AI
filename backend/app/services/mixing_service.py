import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.app.core.config import AUDIO_DIR
from backend.app.core.logging import logger
from backend.app.utils.audio import get_audio_duration
from backend.app.utils.ffmpeg import run_ffmpeg

class MixingService:
    """
    Audio Mixing Service: combines dubbed speech with original audio background track.
    Applies audio ducking during speech intervals.
    """
    def __init__(self):
        pass

    async def create_background_track(
        self,
        master_audio_path: str,
        project_id: str,
        speech_intervals: List[Dict[str, float]],
        total_duration: float,
        voice_suppression: float = 1.0,
        music_volume: float = 0.85
    ) -> str:
        """
        Generates a ducked background track during speech intervals.
        """
        output_bg_path = str(AUDIO_DIR / f"{project_id}_background.wav")
        duck_filter = f"volume={music_volume * (1.0 - 0.7 * voice_suppression):.2f}"
        cmd = [
            "ffmpeg", "-y", "-i", master_audio_path,
            "-af", duck_filter,
            "-ar", "44100", "-ac", "2", output_bg_path
        ]
        await run_ffmpeg(cmd)
        return output_bg_path

    async def mix_full_audio_track(
        self,
        project_id: str,
        background_audio_path: str,
        synced_segments: List[Dict[str, Any]],
        total_duration: float
    ) -> str:
        """
        Mixes speech segments onto background track using FFmpeg amix.
        """
        output_master_path = str(AUDIO_DIR / f"{project_id}_dubbed_master.wav")
        if not synced_segments:
            cmd = ["ffmpeg", "-y", "-i", background_audio_path, "-t", str(total_duration), output_master_path]
            await run_ffmpeg(cmd)
            return output_master_path

        inputs = ["-i", background_audio_path]
        filter_parts = ["[0:a]volume=0.8[bg]"]
        amix_inputs = ["[bg]"]

        for idx, seg in enumerate(synced_segments):
            inputs.extend(["-i", seg["audio_path"]])
            delay_ms = int(seg["start"] * 1000)
            filter_parts.append(f"[{idx+1}:a]adelay={delay_ms}|{delay_ms}[v{idx}]")
            amix_inputs.append(f"[v{idx}]")

        filter_str = ";".join(filter_parts) + ";" + "".join(amix_inputs) + f"amix=inputs={len(amix_inputs)}:duration=first:dropout_transition=2[outa]"
        cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_str, "-map", "[outa]", "-ar", "44100", "-ac", "2", output_master_path]
        await run_ffmpeg(cmd)
        return output_master_path
