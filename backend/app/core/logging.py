import logging
import sys
from datetime import datetime
from typing import Optional

# Setup standard formatting
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ensure UTF-8 output encoding on Windows consoles
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("dubflow")

class StageLogger:
    """
    Dedicated structured logger that formats tags according to requirements:
    [UPLOAD], [EXTRACT], [DIARIZATION], [ASR], [TRANSLATION], [TTS], [SYNC], [MIX], [RENDER], [SYSTEM]
    Includes execution time, GPU memory where applicable, model used, and job IDs.
    """
    def __init__(self, job_id: Optional[str] = None):
        self.job_id = job_id
        self._stage_starts = {}

    def start_stage(self, stage: str):
        self._stage_starts[stage] = datetime.now()
        self.log(stage, f"Started stage {stage}")

    def end_stage(self, stage: str, details: str = ""):
        elapsed = ""
        if stage in self._stage_starts:
            duration = (datetime.now() - self._stage_starts[stage]).total_seconds()
            elapsed = f" completed in {duration:.2f}s"
        self.log(stage, f"Finished stage {stage}{elapsed}. {details}".strip())

    def log(self, stage: str, message: str, level: str = "INFO", gpu_mem: Optional[str] = None, model: Optional[str] = None):
        prefix = f"[{stage.upper()}]"
        job_tag = f"[Job: {self.job_id}]" if self.job_id else ""
        gpu_tag = f"[VRAM: {gpu_mem}]" if gpu_mem else ""
        model_tag = f"[Model: {model}]" if model else ""
        
        full_msg = f"{prefix} {job_tag} {gpu_tag} {model_tag} {message}".replace("   ", " ").replace("  ", " ")
        
        if level == "ERROR":
            logger.error(full_msg)
        elif level == "WARNING":
            logger.warning(full_msg)
        elif level == "DEBUG":
            logger.debug(full_msg)
        else:
            logger.info(full_msg)

app_logger = StageLogger()
