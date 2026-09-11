import asyncio
from typing import List, Dict, Any, Optional
from backend.app.core.logging import logger
from backend.app.providers.local.diarization import LocalDiarizationProvider

class DiarizationService:
    """
    Orchestrates speaker diarization and alignment with transcription lines.
    """
    def __init__(self):
        self.provider = LocalDiarizationProvider()

    async def diarize_audio(
        self,
        audio_path: str,
        transcript_segments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        logger.info(f"[DIARIZATION] Executing speaker diarization pipeline...")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self.provider.diarize, audio_path, transcript_segments)
        logger.info(f"[DIARIZATION] Diarization complete: Found {result['num_speakers']} speaker(s).")
        return result

    def align_transcript_with_speakers(
        self,
        transcript_segments: List[Any],
        diarization_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aligns each transcript line with the dominant speaker during its time window.
        """
        aligned_lines = []
        for line in transcript_segments:
            line_start = line.start
            line_end = line.end
            
            # Find overlapping diarization segments
            best_speaker = "speaker_01"
            max_overlap = 0.0
            best_confidence = line.confidence

            for dseg in diarization_segments:
                d_start = dseg["start"]
                d_end = dseg["end"]
                
                # Overlap between [line_start, line_end] and [d_start, d_end]
                overlap = max(0.0, min(line_end, d_end) - max(line_start, d_start))
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = dseg["speaker"]
                    best_confidence = dseg.get("confidence", line.confidence)

            aligned_lines.append({
                "speaker": best_speaker,
                "start": line_start,
                "end": line_end,
                "text": line.text,
                "confidence": best_confidence
            })
        return aligned_lines

diarization_service = DiarizationService()
