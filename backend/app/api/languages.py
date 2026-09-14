import os
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from backend.app.core.config import VOICES_DIR
from backend.app.services.language_service import language_manager
from backend.app.services.tts_service import tts_service

router = APIRouter(prefix="/api/languages", tags=["languages"])

@router.get("")
def get_languages():
    return language_manager.get_supported_languages()

@router.get("/voices")
async def get_voices(
    language: Optional[str] = Query(None, description="Language name or code (e.g. Arabic, ar)"),
    gender: Optional[str] = Query(None, description="Gender (Male, Female, All)"),
    dialect: Optional[str] = Query(None, description="Country or dialect"),
    search: Optional[str] = Query(None, description="Search keyword")
):
    await language_manager.initialize_all_voices()
    voices = language_manager.filter_voices(language=language, gender=gender, dialect=dialect, search=search)
    return {
        "count": len(voices),
        "voices": voices
    }

@router.get("/voices/{voice_id}/preview")
async def preview_voice(voice_id: str):
    preview_filename = f"preview_{voice_id}.wav"
    preview_path = str(VOICES_DIR / preview_filename)
    if not os.path.exists(preview_path):
        await tts_service.generate_preview_voice(voice_id, preview_path)
    return FileResponse(preview_path, media_type="audio/wav")
