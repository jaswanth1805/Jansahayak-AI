"""Voice Service for Text-to-Speech (TTS).

Converts citizen responses into clear natural speech using Google Text-to-Speech (gTTS),
supporting English, Hindi, and Telugu with local caching and non-blocking asynchronous execution.
"""

import asyncio
import logging
import os
import re
import secrets
import time
from typing import Optional
from gtts import gTTS

from app.config import get_settings

logger = logging.getLogger(__name__)


class VoiceService:
    """Manages audio synthesis, caching, and cleanup for multilingual voice outputs."""

    def __init__(self):
        settings = get_settings()
        self.audio_dir = settings.AUDIO_CACHE_DIR
        os.makedirs(self.audio_dir, exist_ok=True)

    def _get_lang_code(self, lang: str) -> str:
        """Map language input to gTTS supported language codes."""
        code = lang.lower().strip()
        if code in ("hi", "hindi"):
            return "hi"
        elif code in ("te", "telugu"):
            return "te"
        return "en"

    def _clean_for_speech(self, text: str) -> str:
        """Strip markdown syntax and raw URLs to produce clean, natural spoken speech."""
        # Replace [text](url) with just text
        t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Remove URLs
        t = re.sub(r'http[s]?://\S+', '', t)
        # Remove markdown symbols: #, *, `, _, ~, >, |
        t = re.sub(r'[#*`_~>|]', '', t)
        # Remove common emojis
        t = re.sub(r'[💡💰🎯📄📝📋🌾🎓🔊🔍✨]', '', t)
        # Normalize whitespace
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    async def text_to_speech(self, text: str, language: str = "en") -> str:
        """Synthesize text into an MP3 audio file.
        
        Args:
            text: Text to read aloud.
            language: Target ISO code ('en', 'hi', 'te').
            
        Returns:
            Relative endpoint URL path to retrieve the audio (e.g. '/api/voice/audio/<id>').
        """
        clean_text = self._clean_for_speech(text)
        if not clean_text:
            clean_text = text.strip() or "Here is the information you requested."

        # Limit text length for TTS to prevent excessive processing
        if len(clean_text) > 800:
            clean_text = clean_text[:800] + "..."

        target_lang = self._get_lang_code(language)
        
        # Use an unguessable capability: IDs derived from text allow dictionary
        # attacks against cached speech containing personal information.
        audio_id = f"a_{secrets.token_urlsafe(24)}"
        filename = f"{audio_id}.mp3"
        file_path = os.path.join(self.audio_dir, filename)

        # If already cached, return immediately
        if os.path.isfile(file_path):
            return f"/api/voice/audio/{audio_id}"

        # Run CPU-bound/network gTTS call in threadpool
        def _generate():
            tts = gTTS(text=clean_text, lang=target_lang, slow=False)
            tts.save(file_path)

        try:
            await asyncio.to_thread(_generate)
            logger.info("Generated TTS audio '%s' for language '%s'", audio_id, target_lang)
            return f"/api/voice/audio/{audio_id}"
        except Exception as err:
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
            logger.error("gTTS generation error for text (%s): %s", clean_text[:40], err)
            raise RuntimeError(f"Text-to-speech synthesis failed: {err}") from err

    def get_audio_path(self, audio_id: str) -> Optional[str]:
        """Retrieve the absolute disk path for a given audio ID if it exists."""
        # Only accept newly generated, random capability IDs; legacy content hashes
        # are intentionally no longer routable.
        if not re.fullmatch(r"a_[A-Za-z0-9_-]{32}", audio_id):
            return None
        safe_id = f"{audio_id}.mp3"
            
        target_path = os.path.join(self.audio_dir, safe_id)
        if os.path.isfile(target_path):
            return target_path
        return None

    def cleanup_old_audio(self, max_age_hours: int = 2) -> int:
        """Purge cached audio files older than max_age_hours to preserve disk space."""
        if not os.path.exists(self.audio_dir):
            return 0

        cutoff = time.time() - (max_age_hours * 3600)
        removed = 0
        for fname in os.listdir(self.audio_dir):
            if fname.endswith(".mp3"):
                fpath = os.path.join(self.audio_dir, fname)
                try:
                    if os.path.getmtime(fpath) < cutoff:
                        os.remove(fpath)
                        removed += 1
                except Exception as err:
                    logger.debug("Failed removing old audio file %s: %s", fpath, err)
        return removed
