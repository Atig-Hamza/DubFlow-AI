import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, default="Untitled Dub")
    original_video_filename = Column(String, nullable=True)
    original_video_path = Column(String, nullable=True)
    extracted_audio_path = Column(String, nullable=True)
    separated_vocals_path = Column(String, nullable=True)
    separated_background_path = Column(String, nullable=True)
    final_video_path = Column(String, nullable=True)
    
    source_language = Column(String, default="English")
    target_language = Column(String, default="French")
    status = Column(String, default="created")  # created, uploaded, analyzing, analyzed, dubbing, completed, failed
    
    duration = Column(Float, default=0.0)
    width = Column(Integer, default=1920)
    height = Column(Integer, default=1080)
    fps = Column(Float, default=30.0)
    speakers_count = Column(Integer, default=0)

    # Audio mixing parameters
    dialogue_volume = Column(Float, default=1.0)
    music_volume = Column(Float, default=0.85)
    sfx_volume = Column(Float, default=0.85)
    voice_suppression = Column(Float, default=1.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    speakers = relationship("Speaker", back_populates="project", cascade="all, delete-orphan")
    transcript_lines = relationship("TranscriptLine", back_populates="project", cascade="all, delete-orphan", order_by="TranscriptLine.start")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan", order_by="Job.created_at.desc()")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "original_video_filename": self.original_video_filename,
            "original_video_path": self.original_video_path,
            "final_video_path": self.final_video_path,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "status": self.status,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "speakers_count": self.speakers_count,
            "dialogue_volume": self.dialogue_volume,
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "voice_suppression": self.voice_suppression,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
