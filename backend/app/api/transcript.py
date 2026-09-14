from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.models.transcript import TranscriptLine
from backend.app.workers.dubbing_worker import dubbing_worker

router = APIRouter(prefix="/api/projects", tags=["transcript"])

class LineUpdateRequest(BaseModel):
    id: str
    translation: Optional[str] = None
    speaker_id: Optional[str] = None

class TranscriptBulkUpdateRequest(BaseModel):
    lines: List[LineUpdateRequest]

class LineRegenerateRequest(BaseModel):
    translation: Optional[str] = None

@router.get("/{project_id}/transcript")
def get_project_transcript(project_id: str, db: Session = Depends(get_db)):
    lines = db.query(TranscriptLine).filter(TranscriptLine.project_id == project_id).order_by(TranscriptLine.start).all()
    return [l.to_dict() for l in lines]

@router.put("/{project_id}/transcript")
def update_transcript(
    project_id: str,
    req: TranscriptBulkUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Allows bulk editing of dialogue translations or speaker re-assignments.
    """
    updated_count = 0
    for item in req.lines:
        line = db.query(TranscriptLine).filter(
            TranscriptLine.project_id == project_id,
            TranscriptLine.id == item.id
        ).first()
        if line:
            if item.translation is not None:
                line.translation = item.translation
                line.status = "edited"
            if item.speaker_id is not None:
                line.speaker_id = item.speaker_id
            updated_count += 1

    db.commit()
    logger.info(f"[TRANSCRIPT] Updated {updated_count} transcript lines for project {project_id}")
    return {"status": "success", "updated_count": updated_count}

@router.post("/{project_id}/lines/{line_id}/regenerate")
async def regenerate_line(
    project_id: str,
    line_id: str,
    req: Optional[LineRegenerateRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Regenerates voice synthesis and time-sync for an individual dialogue line.
    """
    new_text = req.translation if req else None
    result = await dubbing_worker.run_regenerate_line(project_id, line_id, new_translation=new_text)
    return {
        "status": "success",
        "line": result
    }
