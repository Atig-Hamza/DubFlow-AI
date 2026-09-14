import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.app.core.config import STORAGE_PATH

router = APIRouter(prefix="/api/media", tags=["media"])

@router.get("/{folder}/{filename}")
def get_media_file(folder: str, filename: str):
    allowed_folders = ["uploads", "audio", "segments", "voices", "outputs", "projects"]
    if folder not in allowed_folders:
        raise HTTPException(status_code=400, detail="Invalid folder")

    # Sanitize filename
    safe_filename = Path(filename).name
    file_path = STORAGE_PATH / folder / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Media file not found")

    ext = file_path.suffix.lower()
    media_types = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={"Accept-Ranges": "bytes"}
    )
