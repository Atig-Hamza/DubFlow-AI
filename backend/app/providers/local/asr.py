import os
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.providers.base import ASRProvider, ASRSegment
from backend.app.utils.gpu import clean_vram, get_optimal_device

class LocalWhisperASRProvider(ASRProvider):
    """
    Local Whisper ASR Provider with rigorous VRAM management for RTX A2000 (4GB).
    Loads model on demand -> transcribes -> unloads model -> releases CUDA cache.
    """
    def __init__(self, model_size: Optional[str] = None):
        self.model_size = model_size or settings.WHISPER_MODEL_SIZE
        self.device = get_optimal_device()

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> List[ASRSegment]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"[ASR] Loading Whisper model '{self.model_size}' on {self.device}...")
        
        segments_result: List[ASRSegment] = []
        model = None
        try:
            import whisper
            # FP16 enabled if CUDA is active
            fp16 = (self.device == "cuda") and settings.WHISPER_FP16
            
            try:
                model = whisper.load_model(self.model_size, device=self.device)
            except Exception as cuda_err:
                logger.warning(f"[ASR] CUDA load failed ({cuda_err}), falling back to CPU.")
                self.device = "cpu"
                fp16 = False
                model = whisper.load_model(self.model_size, device="cpu")

            logger.info(f"[ASR] Transcribing audio '{audio_path}' (fp16={fp16})...")
            transcribe_options = {
                "verbose": False,
                "fp16": fp16,
                "task": "transcribe"
            }
            if language and language.lower() != "auto":
                transcribe_options["language"] = language.lower()

            result = model.transcribe(audio_path, **transcribe_options)
            
            detected_lang = result.get("language", "en")
            logger.info(f"[ASR] Detected language: {detected_lang}")

            for seg in result.get("segments", []):
                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", 0.0))
                text = seg.get("text", "").strip()
                # Compute approximate confidence from no_speech_prob and avg_logprob
                no_speech = float(seg.get("no_speech_prob", 0.05))
                confidence = max(0.60, min(0.99, 1.0 - no_speech))
                
                if text:
                    segments_result.append(
                        ASRSegment(
                            start=start,
                            end=end,
                            text=text,
                            confidence=confidence
                        )
                    )

            logger.info(f"[ASR] Transcription completed: {len(segments_result)} segments extracted.")
            return segments_result

        except Exception as e:
            logger.error(f"[ASR] Transcription failed: {e}")
            raise e
        finally:
            # Model lifecycle: immediately unload model from VRAM
            if model is not None:
                del model
            clean_vram()
            logger.info("[ASR] Whisper model unloaded & VRAM cache flushed.")
