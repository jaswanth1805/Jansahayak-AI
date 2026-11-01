"""Chat and Conversational AI API Endpoints.

Provides endpoints for conversational scheme exploration, session state tracking,
and voice transcription with Whisper fallback.
"""

from datetime import datetime, timezone
import io
import logging
import os
import re
import time
import uuid
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, status, Depends
from pydantic import ValidationError

from app.models.schemas import ChatRequest, ChatResponse, ChatMessage, EligibilityProfile, Language
from app.services.llm_service import LLMService
from app.services.government_sources import GovernmentSourceAggregator
from app.services.document_service import DocumentService
from app.services.voice_service import VoiceService
from app.agents.orchestrator import JanSahayakOrchestrator
from app.utils.rate_limit import chat_limit, chat_capacity, voice_capacity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory session store: session_id -> List[ChatMessage]
_SESSION_STORE: Dict[str, List[Dict[str, Any]]] = {}
_SESSION_LAST_ACTIVITY: Dict[str, float] = {}
_SESSION_ID_PATTERN = re.compile(r"^sess_[0-9a-f]{32}$")

# Lazy initialization of orchestrator dependencies
_llm_service = LLMService()
_gov_sources = GovernmentSourceAggregator()
_doc_service = DocumentService(_llm_service)
_voice_service = VoiceService()
_orchestrator = JanSahayakOrchestrator(
    llm_service=_llm_service,
    gov_sources=_gov_sources,
    doc_service=_doc_service,
    voice_service=_voice_service,
)


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _: None = Depends(chat_limit),
    __: None = Depends(chat_capacity),
) -> ChatResponse:
    """Execute main conversational agent turn for JanSahayak AI.
    
    Accepts natural language queries in English, Hindi, or Telugu,
    queries official portals, evaluates criteria, and returns grounded answers.
    """
    session_id = request.session_id if request.session_id and _SESSION_ID_PATTERN.fullmatch(request.session_id) else f"sess_{uuid.uuid4().hex}"
    if request.document_id:
        _doc_service.require_access(request.document_id, request.document_access_token or "")
    user_profile = None
    if request.user_profile is not None:
        try:
            user_profile = EligibilityProfile.model_validate(request.user_profile).model_dump()
        except ValidationError as err:
            raise HTTPException(status_code=422, detail=err.errors()) from err

    now = time.monotonic()
    for old_id, last_seen in list(_SESSION_LAST_ACTIVITY.items()):
        if now - last_seen > 24 * 60 * 60:
            _SESSION_STORE.pop(old_id, None)
            _SESSION_LAST_ACTIVITY.pop(old_id, None)

    # Retrieve or initialize session history
    history = _SESSION_STORE.get(session_id)
    if history is None:
        if len(_SESSION_STORE) >= 1_000 and _SESSION_LAST_ACTIVITY:
            oldest_id = min(_SESSION_LAST_ACTIVITY, key=_SESSION_LAST_ACTIVITY.get)
            _SESSION_STORE.pop(oldest_id, None)
            _SESSION_LAST_ACTIVITY.pop(oldest_id, None)
        history = []
        _SESSION_STORE[session_id] = history
        # Client-supplied history initializes a new session only. Re-appending it
        # on every turn duplicated the entire transcript and caused unbounded growth.
        for m in request.conversation_history:
            history.append({"role": m.role, "content": m.content})
    _SESSION_LAST_ACTIVITY[session_id] = now

    # Record user message
    history.append({"role": "user", "content": request.message})
    if len(history) > 60:
        del history[:-60]

    # Run LangGraph Orchestrator
    result = await _orchestrator.run(
        message=request.message,
        language=request.language.value,
        user_profile=user_profile,
        document_id=request.document_id,
        conversation_history=history,
        include_audio=request.include_audio,
        session_id=session_id,
    )

    # Record assistant message
    history.append({"role": "assistant", "content": result["answer"]})
    if len(history) > 60:
        del history[:-60]

    return ChatResponse(**result)


@router.post("/voice-input")
async def transcribe_voice(
    audio: UploadFile = File(...),
    language: str = "en",
    __: None = Depends(voice_capacity),
) -> Dict[str, Any]:
    """Transcribe spoken citizen audio using OpenAI Whisper API if configured.
    
    Falls back with guidance to browser-side Web Speech API if API key is not present.
    """
    if not _llm_service._is_valid_key(_llm_service.openai_key):
        return {
            "success": False,
            "transcription": "",
            "message": "OpenAI Whisper is not configured on server. Please use browser Web Speech API for voice input."
        }

    try:
        from app.config import get_settings
        content = await audio.read(get_settings().max_upload_size_bytes + 1)
        if len(content) > get_settings().max_upload_size_bytes:
            raise HTTPException(status_code=413, detail="Audio upload exceeds the configured size limit.")
        file_obj = io.BytesIO(content)
        file_obj.name = audio.filename or "recording.webm"

        # Map language code for Whisper
        whisper_lang = "hi" if language == "hi" else ("te" if language == "te" else "en")

        client = _llm_service.openai_client
        if client is None:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=_llm_service.openai_key, timeout=30.0)
            _llm_service.openai_client = client

        transcription = await client.audio.transcriptions.create(
            model="whisper-1",
            file=file_obj,
            language=whisper_lang,
        )

        return {
            "success": True,
            "transcription": transcription.text,
            "language": language,
            "filename": audio.filename,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Whisper transcription failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice transcription failed. Please retry or use browser speech recognition."
        )


@router.get("/session/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """Retrieve full conversation history for a given session identifier."""
    if not _SESSION_ID_PATTERN.fullmatch(session_id) or session_id not in _SESSION_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )

    return {
        "session_id": session_id,
        "messages": _SESSION_STORE[session_id],
        "total_messages": len(_SESSION_STORE[session_id]),
    }


@router.delete("/session/{session_id}")
async def clear_session(session_id: str) -> Dict[str, Any]:
    """Clear conversation history for a session."""
    if _SESSION_ID_PATTERN.fullmatch(session_id) and session_id in _SESSION_STORE:
        del _SESSION_STORE[session_id]
        _SESSION_LAST_ACTIVITY.pop(session_id, None)
        return {"success": True, "message": f"Session '{session_id}' cleared."}
    return {"success": False, "message": "Session did not exist."}
