import os
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.models.project import Project
from backend.app.models.job import Job
from backend.app.workers.dubbing_worker import dubbing_worker

router = APIRouter(prefix="/api/projects", tags=["dubbing"])

class DubRequest(BaseModel):
    dialogue_volume: Optional[float] = 1.0
    music_volume: Optional[float] = 0.85
    sfx_volume: Optional[float] = 0.85
    voice_suppression: Optional[float] = 1.0

@router.post("/{project_id}/analyze")
async def analyze_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Triggers the video analysis pipeline: audio extraction, ASR, diarization, speaker profiling, and initial translation.
    Returns immediately with job_id.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.original_video_path or not os.path.exists(project.original_video_path):
        raise HTTPException(status_code=400, detail="Please upload a video before analyzing.")

    # Create Job record
    job = Job(
        project_id=project_id,
        job_type="analyze",
        status="processing",
        current_stage="Extracting audio",
        progress_percent=5
    )
    job.add_log("Extracting audio", "Job initialized, extracting audio...")
    db.add(job)
    project.status = "analyzing"
    db.commit()
    db.refresh(job)

    # Launch in background
    background_tasks.add_task(dubbing_worker.run_analyze_pipeline, project_id, job.id)

    return {
        "job_id": job.id,
        "status": "processing",
        "message": "Analysis started in background"
    }

@router.post("/{project_id}/dub")
async def start_dubbing(
    project_id: str,
    req: Optional[DubRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Triggers the full dubbing pipeline: multi-speaker TTS, timing synchronization, audio mixing, and video rendering.
    Returns immediately with job_id.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.transcript_lines:
        raise HTTPException(status_code=400, detail="Project must be analyzed before starting dubbing.")

    # Update audio mixing parameters if provided
    if req:
        if req.dialogue_volume is not None:
            project.dialogue_volume = req.dialogue_volume
        if req.music_volume is not None:
            project.music_volume = req.music_volume
        if req.sfx_volume is not None:
            project.sfx_volume = req.sfx_volume
        if req.voice_suppression is not None:
            project.voice_suppression = req.voice_suppression

    # Create Job record
    job = Job(
        project_id=project_id,
        job_type="dub",
        status="processing",
        current_stage="Generating voices",
        progress_percent=5
    )
    job.add_log("Generating voices", "Starting multi-speaker synthesis...")
    db.add(job)
    project.status = "dubbing"
    db.commit()
    db.refresh(job)

    # Launch in background
    background_tasks.add_task(dubbing_worker.run_dubbing_pipeline, project_id, job.id)

    return {
        "job_id": job.id,
        "status": "processing",
        "message": "Dubbing pipeline started in background"
    }

@router.get("/{project_id}/output")
def get_project_output(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.final_video_path or not os.path.exists(project.final_video_path):
        raise HTTPException(status_code=404, detail="Dubbed video output has not been rendered yet.")

    return FileResponse(
        path=project.final_video_path,
        media_type="video/mp4",
        filename=f"dubbed_{project.name.replace(' ', '_')}.mp4"
    )
