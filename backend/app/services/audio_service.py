import os
from pathlib import Path
from backend.app.core.config import AUDIO_DIR
from backend.app.core.logging import logger
from backend.app.utils.ffmpeg import run_ffmpeg

class AudioService:
    """
    Extracts high-quality WAV audio from video files and handles audio preprocessing.
    """
    def __init__(self):
        pass

    async def extract_audio_from_video(self, video_path: str, project_id: str) -> str:
        """
        Extracts 16kHz mono audio (ideal for ASR & Diarization) from the video.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        output_wav = str(AUDIO_DIR / f"{project_id}_16k_mono.wav")
        
        logger.info(f"[EXTRACT] Extracting audio from '{video_path}' to '{output_wav}'...")
        await run_ffmpeg([
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_wav
        ])
        logger.info(f"[EXTRACT] Audio extracted successfully.")
        return output_wav

    async def extract_master_stereo_audio(self, video_path: str, project_id: str) -> str:
        """
        Extracts 44.1kHz Stereo audio for background music/SFX preservation and final mixing.
        """
        output_wav = str(AUDIO_DIR / f"{project_id}_master_stereo.wav")
        logger.info(f"[EXTRACT] Extracting master stereo audio for mixing to '{output_wav}'...")
        await run_ffmpeg([
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            output_wav
        ])
        return output_wav

audio_service = AudioService()
