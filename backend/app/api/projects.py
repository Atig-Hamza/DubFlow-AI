import os
import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.config import UPLOADS_DIR
from backend.app.core.logging import logger
from backend.app.models.project import Project
from backend.app.models.speaker import Speaker
from backend.app.models.transcript import TranscriptLine
from backend.app.models.job import Job

router = APIRouter(prefix="/api/projects", tags=["projects"])

class ProjectCreateRequest(BaseModel):
    name: Optional[str] = "Untitled Dub"
    source_language: Optional[str] = "English"
    target_language: Optional[str] = "French"

@router.post("")
def create_project(req: ProjectCreateRequest, db: Session = Depends(get_db)):
    project = Project(
        name=req.name or "Untitled Dub",
        source_language=req.source_language or "English",
        target_language=req.target_language or "French",
        status="created"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info(f"[PROJECT] Created project {project.id}: '{project.name}'")
    return project.to_dict()

@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).limit(20).all()
    return [p.to_dict() for p in projects]

@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    data = project.to_dict()
    data["speakers"] = [s.to_dict() for s in project.speakers]
    data["transcript"] = [t.to_dict() for t in project.transcript_lines]
    data["jobs"] = [j.to_dict() for j in project.jobs]
    return data

@router.post("/{project_id}/upload")
async def upload_video(
    project_id: str,
    file: UploadFile = File(...),
    target_language: Optional[str] = Form(None),
    source_language: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts video upload and saves to storage/uploads.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    allowed_exts = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported format {ext}. Allowed: {allowed_exts}")

    filename = f"{project_id}_{file.filename.replace(' ', '_')}"
    save_path = str(UPLOADS_DIR / filename)

    logger.info(f"[UPLOAD] Uploading video for project {project_id}: {file.filename} -> {save_path}")

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    project.original_video_filename = file.filename
    project.original_video_path = save_path
    project.status = "uploaded"
    if target_language:
        project.target_language = target_language
    if source_language:
        project.source_language = source_language

    db.commit()
    db.refresh(project)
    return project.to_dict()

@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"status": "success", "message": f"Project {project_id} deleted"}
