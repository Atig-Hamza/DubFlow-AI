import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.config import VOICES_DIR
from backend.app.core.logging import logger
from backend.app.models.speaker import Speaker
from backend.app.models.project import Project
from backend.app.services.tts_service import tts_service

router = APIRouter(prefix="/api/projects", tags=["speakers"])

class SpeakerUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    assigned_voice_id: Optional[str] = None
    voice_consent: Optional[bool] = None

@router.get("/{project_id}/speakers")
def get_project_speakers(project_id: str, db: Session = Depends(get_db)):
    speakers = db.query(Speaker).filter(Speaker.project_id == project_id).all()
    return [s.to_dict() for s in speakers]

@router.post("/{project_id}/speakers/{speaker_id}/voice")
def update_speaker_voice(
    project_id: str,
    speaker_id: str,
    req: SpeakerUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Allows the user to rename the speaker, select an alternative AI voice, and provide consent.
    """
    speaker = db.query(Speaker).filter(
        Speaker.project_id == project_id,
        (Speaker.id == speaker_id) | (Speaker.speaker_tag == speaker_id)
    ).first()

    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")

    if req.display_name is not None:
        speaker.display_name = req.display_name.strip()
    if req.assigned_voice_id is not None:
        speaker.assigned_voice_id = req.assigned_voice_id.strip()
    if req.voice_consent is not None:
        speaker.voice_consent = req.voice_consent

    db.commit()
    db.refresh(speaker)
    logger.info(f"[SPEAKER] Updated {speaker.speaker_tag}: name='{speaker.display_name}', voice='{speaker.assigned_voice_id}'")
    return speaker.to_dict()

@router.get("/{project_id}/speakers/{speaker_id}/preview")
async def preview_speaker_voice(
    project_id: str,
    speaker_id: str,
    db: Session = Depends(get_db)
):
    """
    Generates and streams an instantaneous voice preview using the speaker's assigned AI voice.
    """
    speaker = db.query(Speaker).filter(
        Speaker.project_id == project_id,
        (Speaker.id == speaker_id) | (Speaker.speaker_tag == speaker_id)
    ).first()

    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")

    voice_id = speaker.assigned_voice_id or "fr-FR-HenriNeural"
    preview_filename = f"preview_{voice_id}.wav"
    preview_path = str(VOICES_DIR / preview_filename)

    if not os.path.exists(preview_path):
        sample_phrase = f"Hello! This is an AI voice preview for {speaker.display_name} in DubFlow."
        await tts_service.generate_preview_voice(voice_id, preview_path, sample_phrase)

    return FileResponse(preview_path, media_type="audio/wav")
