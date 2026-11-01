"""JanSahayak AI Backend Application Entrypoint.

JanSahayak AI (जनसहायक) is a multilingual, citizen-first AI assistant that demystifies
Indian Government policies, welfare schemes, eligibility criteria, and citizen entitlements
using grounded RAG, official government API integrations, and LangGraph workflow orchestration.
"""

from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timezone
import logging
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
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
from app.utils.rate_limit import upload_gate, upload_limit, voice_limit


class APIRequestSizeLimitMiddleware:
    """Bound bodies before FastAPI's multipart parser spools uploads to disk."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith("/api/"):
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        path = scope.get("path", "")
        is_file_upload = path in {"/api/documents/upload", "/api/chat/voice-input"}
        limit = settings.max_upload_size_bytes + 1024 * 1024 if is_file_upload else 2 * 1024 * 1024
        if scope.get("method") not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        limiter = (
            upload_limit if path == "/api/documents/upload"
            else voice_limit if path == "/api/chat/voice-input"
            else None
        )
        if limiter:
            try:
                await limiter(Request(scope, receive=receive))
            except HTTPException as exc:
                response = JSONResponse(
                    {"detail": exc.detail},
                    status_code=exc.status_code,
                    headers=exc.headers,
                )
                await response(scope, receive, send)
                return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                if int(content_length) > limit:
                    response = JSONResponse({"detail": "Request body exceeds the configured size limit."}, status_code=413)
                    await response(scope, receive, send)
                    return
            except ValueError:
                response = JSONResponse({"detail": "Invalid Content-Length header."}, status_code=400)
                await response(scope, receive, send)
                return

        total = 0
        response_started = False

        async def limited_receive():
            nonlocal total
            message = await receive()
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                if total > limit:
                    raise HTTPException(
                        status_code=413,
                        detail="Request body exceeds the configured size limit.",
                    )
            return message

        async def tracked_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            if is_file_upload:
                async with upload_gate.enter():
                    await self.app(scope, limited_receive, tracked_send)
            else:
                await self.app(scope, limited_receive, tracked_send)
        except HTTPException as exc:
            if not response_started:
                response = JSONResponse(
                    {"detail": exc.detail},
                    status_code=exc.status_code,
                    headers=exc.headers,
                )
                await response(scope, receive, send)
async def _retention_maintenance(retention_hours: int) -> None:
    """Enforce document/audio retention during long-running server processes."""
    interval = min(3600, max(60, retention_hours * 3600 // 4))
    while True:
        await asyncio.sleep(interval)
        try:
            settings = get_settings()
            await asyncio.to_thread(cleanup_old_files, settings.UPLOAD_DIR, retention_hours)
            await asyncio.to_thread(VoiceService().cleanup_old_audio, retention_hours)
            from app.api.documents import _doc_service
            # Orphan sweeps run at startup only; doing them periodically could
            # race an upload that has indexed vectors but not registered yet.
            await asyncio.to_thread(_doc_service.cleanup_expired_documents, retention_hours, False)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Periodic document retention maintenance failed")


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

    # Initial housekeeping. Vector data and the source PDF share the same retention.
    VoiceService().cleanup_old_audio(max_age_hours=settings.DOCUMENT_RETENTION_HOURS)
    cleanup_old_files(settings.UPLOAD_DIR, max_age_hours=settings.DOCUMENT_RETENTION_HOURS)
    try:
        from app.api.documents import _doc_service
        await asyncio.to_thread(
            _doc_service.cleanup_expired_documents,
            settings.DOCUMENT_RETENTION_HOURS,
        )
    except Exception:
        logger.exception("Document retention cleanup failed during startup")

    retention_task = asyncio.create_task(
        _retention_maintenance(settings.DOCUMENT_RETENTION_HOURS)
    )
    logger.info("JanSahayak AI Backend is ready to serve citizen queries.")
    try:
        yield
    finally:
        retention_task.cancel()
        try:
            await retention_task
        except asyncio.CancelledError:
            pass
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
app.add_middleware(APIRequestSizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat.router)
app.include_router(schemes.router)
app.include_router(eligibility.router)
app.include_router(documents.router)
app.include_router(voice.router)

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
    storage_ready = all(
        os.path.isdir(path)
        for path in (settings.UPLOAD_DIR, settings.AUDIO_CACHE_DIR, settings.CHROMADB_PATH)
    )

    return {
        # This endpoint reports application/storage readiness. Provider
        # reachability is intentionally not probed on every health request.
        "status": "healthy" if storage_ready else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm_service": llm_status,
        "storage": {
            "upload_dir_ready": os.path.isdir(settings.UPLOAD_DIR),
            "audio_cache_ready": os.path.isdir(settings.AUDIO_CACHE_DIR),
            "chroma_db_ready": os.path.isdir(settings.CHROMADB_PATH),
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
