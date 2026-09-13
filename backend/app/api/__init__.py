from backend.app.api.projects import router as projects_router
from backend.app.api.dubbing import router as dubbing_router
from backend.app.api.speakers import router as speakers_router
from backend.app.api.transcript import router as transcript_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.diagnostics import router as diagnostics_router
from backend.app.api.languages import router as languages_router
from backend.app.api.media import router as media_router

__all__ = [
    "projects_router",
    "dubbing_router",
    "speakers_router",
    "transcript_router",
    "jobs_router",
    "diagnostics_router",
    "languages_router",
    "media_router"
]
