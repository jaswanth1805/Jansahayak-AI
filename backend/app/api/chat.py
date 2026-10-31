"""Chat and Conversational AI API Endpoints.

Provides endpoints for conversational scheme exploration, session state tracking,
and voice transcription with Whisper fallback.
"""

from datetime import datetime, timezone
import io
import logging
import os
import uuid
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, status

from app.models.schemas import ChatRequest, ChatResponse, ChatMessage, Language
from app.services.llm_service import LLMService
from app.services.government_sources import GovernmentSourceAggregator
from app.services.document_service import DocumentService
from app.services.voice_service import VoiceService
from app.agents.orchestrator import JanSahayakOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory session store: session_id -> List[ChatMessage]
_SESSION_STORE: Dict[str, List[Dict[str, Any]]] = {}

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
async def chat(request: ChatRequest) -> ChatResponse:
    """Execute main conversational agent turn for JanSahayak AI.
    
    Accepts natural language queries in English, Hindi, or Telugu,
    queries official portals, evaluates criteria, and returns grounded answers.
    """
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    # Retrieve or initialize session history
    history = _SESSION_STORE.setdefault(session_id, [])

    # Merge incoming conversation_history if supplied
    if request.conversation_history:
        for m in request.conversation_history:
            history.append({"role": m.role, "content": m.content})

    # Record user message
    history.append({"role": "user", "content": request.message})

    # Run LangGraph Orchestrator
    result = await _orchestrator.run(
        message=request.message,
        language=request.language.value,
        user_profile=None,
        document_id=request.document_id,
        conversation_history=history,
        include_audio=request.include_audio,
        session_id=session_id,
    )

    # Record assistant message
    history.append({"role": "assistant", "content": result["answer"]})

    return ChatResponse(**result)


@router.post("/voice-input")
async def transcribe_voice(
    audio: UploadFile = File(...),
    language: str = "en"
) -> Dict[str, Any]:
    """Transcribe spoken citizen audio using OpenAI Whisper API if configured.
    
    Falls back with guidance to browser-side Web Speech API if API key is not present.
    """
    if not _llm_service.is_configured():
        return {
            "success": False,
            "transcription": "",
            "message": "OpenAI Whisper is not configured on server. Please use browser Web Speech API for voice input."
        }

    try:
        content = await audio.read()
        file_obj = io.BytesIO(content)
        file_obj.name = audio.filename or "recording.webm"

        # Map language code for Whisper
        whisper_lang = "hi" if language == "hi" else ("te" if language == "te" else "en")

        client = _llm_service.client
        if client is None:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=_llm_service.api_key)

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
    except Exception as e:
        logger.error("Whisper transcription failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice transcription failed: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """Retrieve full conversation history for a given session identifier."""
    if session_id not in _SESSION_STORE:
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
    if session_id in _SESSION_STORE:
        del _SESSION_STORE[session_id]
        return {"success": True, "message": f"Session '{session_id}' cleared."}
    return {"success": False, "message": "Session did not exist."}
