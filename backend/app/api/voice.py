"""Voice and Audio Streaming API Endpoints.

Provides text-to-speech synthesis and MP3 audio streaming for accessibility
in English, Hindi, and Telugu.
"""

import logging
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.models.schemas import VoiceRequest, VoiceResponse
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])
_voice_service = VoiceService()


@router.post("/synthesize", response_model=VoiceResponse)
async def synthesize_speech(request: VoiceRequest) -> VoiceResponse:
    """Convert text to spoken MP3 audio in English, Hindi, or Telugu.
    
    Returns URL to stream the synthesized audio file.
    """
    try:
        audio_url = await _voice_service.text_to_speech(
            text=request.text,
            language=request.language.value,
        )
        return VoiceResponse(
            audio_url=audio_url,
            duration_seconds=round(len(request.text.split()) / 2.5, 1),
            language=request.language,
        )
    except Exception as e:
        logger.error("Speech synthesis failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis error: {str(e)}"
        )


@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    """Stream a synthesized MP3 audio file by ID."""
    audio_path = _voice_service.get_audio_path(audio_id)
    if not audio_path or not os.path.isfile(audio_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file '{audio_id}' not found or expired."
        )

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=os.path.basename(audio_path),
        headers={"Accept-Ranges": "bytes"}
    )
