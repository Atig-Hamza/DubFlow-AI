import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings, BASE_DIR
from backend.app.core.database import init_db
from backend.app.core.logging import logger
from backend.app.api import (
    projects_router,
    dubbing_router,
    speakers_router,
    transcript_router,
    jobs_router,
    diagnostics_router,
    languages_router,
    media_router
)

# Initialize database schema
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered video dubbing SaaS platform with multi-speaker diarization, NVIDIA translation, neural TTS, timing synchronization, and background audio preservation."
)

# Enable CORS for seamless local and cloud deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API Routers
app.include_router(projects_router)
app.include_router(dubbing_router)
app.include_router(speakers_router)
app.include_router(transcript_router)
app.include_router(jobs_router)
app.include_router(diagnostics_router)
app.include_router(languages_router)
app.include_router(media_router)

# Direct alias for /api/voices
from backend.app.api.languages import get_voices, preview_voice
app.add_api_route("/api/voices", get_voices, methods=["GET"], tags=["languages"])
app.add_api_route("/api/voices/{voice_id}/preview", preview_voice, methods=["GET"], tags=["languages"])

# Mount Frontend static assets
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_frontend():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "DubFlow AI Backend is running. Frontend index.html not found."}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "device": settings.DEVICE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
