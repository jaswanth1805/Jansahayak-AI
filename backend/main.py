"""JanSahayak AI Backend Application Entrypoint.

JanSahayak AI (जनसहायक) is a multilingual, citizen-first AI assistant that demystifies
Indian Government policies, welfare schemes, eligibility criteria, and citizen entitlements
using grounded RAG, official government API integrations, and LangGraph workflow orchestration.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Configure root logger with timestamps and module labels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("jansahayak")

from app.config import get_settings
from app.api import chat, schemes, eligibility, documents, voice
from app.services.voice_service import VoiceService
from app.utils.file_utils import cleanup_old_files


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management for JanSahayak AI.
    
    Creates required runtime storage directories, verifies connectivity,
    and runs startup/shutdown resource cleanup.
    """
    settings = get_settings()
    logger.info("Initializing JanSahayak AI Backend (Environment: %s)", "Debug" if settings.DEBUG else "Production")

    # Ensure required persistence directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)
    os.makedirs(settings.CHROMADB_PATH, exist_ok=True)

    # Initial housekeeping
    VoiceService().cleanup_old_audio(max_age_hours=24)
    cleanup_old_files(settings.UPLOAD_DIR, max_age_hours=24)

    logger.info("JanSahayak AI Backend is ready to serve citizen queries.")
    yield
    logger.info("JanSahayak AI Backend shutting down.")


settings = get_settings()

app = FastAPI(
    title="JanSahayak AI API",
    description="Multilingual Indian Government Policy, Scheme & Entitlement Explainer API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS) for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat.router)
app.include_router(schemes.router)
app.include_router(eligibility.router)
app.include_router(documents.router)
app.include_router(voice.router)

# Mount audio cache directory for static fallback access
os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)
app.mount("/static/audio", StaticFiles(directory=settings.AUDIO_CACHE_DIR), name="audio_static")


@app.get("/", tags=["system"])
async def root():
    """Root health and service information endpoint."""
    return {
        "service": "JanSahayak AI API",
        "description": "Multilingual Indian Government Scheme & Entitlement Explainer",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "documentation": "/docs",
        "supported_languages": ["en (English)", "hi (Hindi - हिंदी)", "te (Telugu - తెలుగు)"],
    }


@app.get("/health", tags=["system"])
async def health_check():
    """Comprehensive system readiness and health diagnostic check."""
    from app.services.llm_service import LLMService
    llm_status = await LLMService().check_api_status()

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm_service": llm_status,
        "storage": {
            "upload_dir_ready": os.path.exists(settings.UPLOAD_DIR),
            "audio_cache_ready": os.path.exists(settings.AUDIO_CACHE_DIR),
            "chroma_db_ready": os.path.exists(settings.CHROMADB_PATH),
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
