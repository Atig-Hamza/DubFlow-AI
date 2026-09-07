import json
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String, default="dub")  # "analyze", "dub", "regenerate_line"
    status = Column(String, default="queued")  # "queued", "processing", "completed", "failed", "cancelled"
    current_stage = Column(String, default="Uploading")
    progress_percent = Column(Integer, default=0)
    
    # Store JSON array of logs
    logs_json = Column(Text, default="[]")
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="jobs")

    def add_log(self, stage: str, message: str):
        logs = json.loads(self.logs_json) if self.logs_json else []
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        logs.append({
            "timestamp": timestamp,
            "stage": stage,
            "message": message
        })
        self.logs_json = json.dumps(logs)

    def get_logs(self):
        return json.loads(self.logs_json) if self.logs_json else []

    def to_dict(self):
        return {
            "job_id": self.id,
            "project_id": self.project_id,
            "job_type": self.job_type,
            "status": self.status,
            "current_stage": self.current_stage,
            "progress": self.progress_percent,
            "error": self.error_message,
            "logs": self.get_logs(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
