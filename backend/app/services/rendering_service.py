import os
from pathlib import Path
from backend.app.core.config import OUTPUTS_DIR
from backend.app.core.logging import logger
from backend.app.utils.ffmpeg import run_ffmpeg, probe_file

class RenderingService:
    """
    Renders the final dubbed video by muxing the mixed audio track with the original video stream.
    Prioritizes stream copying (-c:v copy) to preserve resolution and framerate without quality loss.
    """
    def __init__(self):
        pass

    async def render_dubbed_video(
        self,
        video_path: str,
        audio_path: str,
        project_id: str
    ) -> str:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Original video not found: {video_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio mix track not found: {audio_path}")

        output_video_path = str(OUTPUTS_DIR / f"{project_id}_dubbed.mp4")
        logger.info(f"[RENDER] Reconstructing final video: '{output_video_path}'...")

        # Probe video info
        info = probe_file(video_path)
        video_codec = info.get("video_codec", "")

        # Try fast stream copy first
        copy_success = False
        try:
            logger.info("[RENDER] Attempting direct stream copy (-c:v copy)...")
            await run_ffmpeg([
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-movflags", "+faststart",
                "-shortest",
                output_video_path
            ])
            copy_success = True
            logger.info("[RENDER] Direct stream copy successful.")
        except Exception as copy_err:
            logger.warning(f"[RENDER] Direct copy failed ({copy_err}), falling back to libx264 re-encoding...")

        if not copy_success:
            # Fallback to high-quality re-encoding with libx264
            await run_ffmpeg([
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-movflags", "+faststart",
                "-shortest",
                output_video_path
            ])
            logger.info("[RENDER] Re-encoding completed.")

        return output_video_path

rendering_service = RenderingService()
