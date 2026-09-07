import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class TranscriptLine(Base):
    __tablename__ = "transcript_lines"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    speaker_id = Column(String, nullable=False)  # speaker_tag e.g., "speaker_01"
    
    start = Column(Float, nullable=False)  # in seconds
    end = Column(Float, nullable=False)    # in seconds
    original_text = Column(Text, nullable=False)
    translation = Column(Text, nullable=True)
    confidence = Column(Float, default=0.95)
    
    # Audio generation and sync
    generated_audio_path = Column(String, nullable=True)
    synchronized_audio_path = Column(String, nullable=True)
    time_stretch_ratio = Column(Float, default=1.0)
    status = Column(String, default="ready")  # ready, processing, dubbed, edited, failed

    project = relationship("Project", back_populates="transcript_lines")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "speaker_id": self.speaker_id,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "duration": round(self.end - self.start, 2),
            "original": self.original_text,
            "translation": self.translation or "",
            "confidence": round(self.confidence * 100, 1),
            "generated_audio_path": self.generated_audio_path,
            "synchronized_audio_path": self.synchronized_audio_path,
            "status": self.status,
        }
