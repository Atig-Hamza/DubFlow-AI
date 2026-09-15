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
    Applies audio time stretching (atempo/librubberband), padding, and duration matching.
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
        Adjusts generated audio to fit naturally within the target window without truncating sentences.
        If speech is longer, gently accelerates (atempo up to 1.35x) and expands into the gap
        before the next speaker starts, guaranteeing every word is spoken completely.
        """
        if not os.path.exists(raw_audio_path):
            raise FileNotFoundError(f"Raw audio segment not found: {raw_audio_path}")

        target_duration = max(0.4, target_end - target_start)
        actual_duration = get_audio_duration(raw_audio_path)

        synced_filename = f"{project_id}_{line_id}_synced.wav"
        synced_path = str(SEGMENTS_DIR / synced_filename)

        if actual_duration <= 0.05:
            logger.warning(f"[SYNC] Actual duration too short ({actual_duration}s), copying as-is.")
            return {
                "synced_path": raw_audio_path,
                "ratio": 1.0,
                "final_duration": target_duration
            }

        # Determine available time budget before next speaker or video boundary
        if next_start is not None and next_start > target_start:
            # Leave 50ms breathing gap before next speaker starts
            available_budget = max(target_duration, (next_start - target_start) - 0.05)
        elif max_duration is not None and max_duration > target_start:
            available_budget = max(target_duration, (max_duration - target_start) - 0.05)
        else:
            available_budget = target_duration + 1.5

        logger.info(
            f"[SYNC] Line {line_id}: target={target_duration:.2f}s, budget={available_budget:.2f}s, actual={actual_duration:.2f}s"
        )

        # Compute optimal tempo factor
        # If speech exceeds available budget, accelerate up to 1.38x to fit
        if actual_duration > available_budget:
            speed_factor = min(1.38, max(1.0, actual_duration / available_budget))
        elif actual_duration > target_duration:
            # Fits in budget but exceeds target: gentle speedup (1.10x - 1.25x)
            speed_factor = min(1.25, max(1.0, actual_duration / target_duration))
        elif actual_duration < target_duration * 0.75:
            # Very short line: slow down gently for natural articulation
            speed_factor = max(0.88, actual_duration / target_duration)
        else:
            speed_factor = 1.0

        # Build FFmpeg atempo filter chain
        # Note: We NEVER use atrim on spoken lines so complete sentences are guaranteed!
        filter_chain = f"atempo={speed_factor:.3f}"
        
        # If speed adjusted audio is shorter than target, pad with silence to target
        speed_adjusted_duration = actual_duration / speed_factor
        if speed_adjusted_duration < target_duration:
            filter_chain += f",apad=whole_dur={target_duration:.3f}"

        ffmpeg_args = [
            "-i", raw_audio_path,
            "-filter:a", filter_chain,
            "-ar", "24000",
            "-ac", "1",
            synced_path
        ]

        await run_ffmpeg(ffmpeg_args)
        final_duration = get_audio_duration(synced_path)
        logger.info(f"[SYNC] Line {line_id} complete sentence preserved: {final_duration:.2f}s (tempo: {speed_factor:.2f}x).")

        return {
            "synced_path": synced_path,
            "ratio": round(speed_factor, 2),
            "final_duration": round(final_duration, 2)
        }

synchronization_service = SynchronizationService()
