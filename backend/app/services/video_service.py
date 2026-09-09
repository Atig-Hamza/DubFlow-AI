import os
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.core.config import UPLOADS_DIR, OUTPUTS_DIR
from backend.app.core.logging import logger
from backend.app.utils.ffmpeg import probe_file, run_ffmpeg

class VideoService:
    """
    Handles video inspection, thumbnail generation, and metadata extraction.
    """
    def __init__(self):
        pass

    def inspect_video(self, video_path: str) -> Dict[str, Any]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        info = probe_file(video_path)
        logger.info(f"[VIDEO] Inspected {video_path}: {info['duration']}s, {info['width']}x{info['height']} @ {info['fps']}fps")
        return info

    async def generate_thumbnail(self, video_path: str, output_path: str, timestamp_sec: float = 1.0) -> str:
        """
        Generates a JPEG thumbnail from the video for UI preview.
        """
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        await run_ffmpeg([
            "-ss", str(timestamp_sec),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ])
        return output_path

video_service = VideoService()
