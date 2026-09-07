import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Speaker(Base):
    __tablename__ = "speakers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    speaker_tag = Column(String, nullable=False)  # e.g., "speaker_01"
    display_name = Column(String, nullable=False)  # e.g., "Speaker 01" or "John"
    
    segments_count = Column(Integer, default=0)
    total_speech_time = Column(Float, default=0.0)  # In seconds
    avg_pitch = Column(Float, default=160.0)  # In Hz
    speaking_rate = Column(Float, default=140.0)  # Syllables or Words/min
    loudness = Column(Float, default=-20.0)  # In dBFS
    gender_detected = Column(String, default="Unknown")  # Male, Female, Unknown
    confidence = Column(Float, default=0.90)  # 0.0 to 1.0
    
    sample_audio_path = Column(String, nullable=True)  # Clean sample clip
    assigned_voice_id = Column(String, nullable=True)  # E.g., fr-FR-HenriNeural
    voice_consent = Column(Boolean, default=True)

    project = relationship("Project", back_populates="speakers")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "speaker_tag": self.speaker_tag,
            "display_name": self.display_name,
            "segments_count": self.segments_count,
            "total_speech_time": self.total_speech_time,
            "avg_pitch": round(self.avg_pitch, 1),
            "speaking_rate": round(self.speaking_rate, 1),
            "loudness": round(self.loudness, 1),
            "gender_detected": self.gender_detected,
            "confidence": round(self.confidence * 100, 1),
            "sample_audio_path": self.sample_audio_path,
            "assigned_voice_id": self.assigned_voice_id,
            "voice_consent": self.voice_consent,
        }
