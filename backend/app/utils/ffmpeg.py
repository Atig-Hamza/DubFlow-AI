import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from backend.app.core.logging import logger

def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None

def get_ffmpeg_version() -> str:
    if not is_ffmpeg_available():
        return "Not installed"
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        first_line = res.stdout.splitlines()[0]
        return first_line
    except Exception as e:
        return f"Error: {e}"

def probe_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    file_path = str(file_path)
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        
        format_info = data.get("format", {})
        duration = float(format_info.get("duration", 0.0))
        
        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
        
        width = int(video_stream.get("width", 1920)) if video_stream else 1920
        height = int(video_stream.get("height", 1080)) if video_stream else 1080
        
        # Calculate fps
        fps = 30.0
        if video_stream and "r_frame_rate" in video_stream:
            num, den = video_stream["r_frame_rate"].split("/")
            fps = float(num) / float(den) if float(den) > 0 else 30.0

        return {
            "duration": duration,
            "width": width,
            "height": height,
            "fps": round(fps, 2),
            "has_video": video_stream is not None,
            "has_audio": audio_stream is not None,
            "video_codec": video_stream.get("codec_name") if video_stream else None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        }
    except Exception as e:
        logger.error(f"[FFMPEG] ffprobe failed for {file_path}: {e}")
        return {
            "duration": 0.0,
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "has_video": True,
            "has_audio": True,
            "error": str(e)
        }

async def run_ffmpeg(args: List[str]) -> bool:
    cmd = ["ffmpeg", "-y"] + args
    logger.debug(f"[FFMPEG] Running: {' '.join(cmd)}")
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    
    if proc.returncode != 0:
        err_msg = stderr.decode(errors='replace')
        logger.error(f"[FFMPEG] Command failed with code {proc.returncode}: {err_msg[:400]}")
        raise RuntimeError(f"FFmpeg error: {err_msg[:200]}")
    
    return True
