"""Multilingual Language Utilities.

Provides language identification, script-based fallback detection,
and deep-translation capabilities supporting English, Hindi, and Telugu.
"""

import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)

# Supported languages metadata
LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
}

LANGUAGE_PROMPTS: Dict[str, str] = {
    "en": "Respond in simple, clear English that ordinary citizens can understand.",
    "hi": "हिंदी में सरल और स्पष्ट भाषा में उत्तर दें जो आम नागरिक समझ सकें।",
    "te": "సాధారణ పౌరులు అర్థం చేసుకోగలిగేలా సరళమైన, స్పష్టమైన తెలుగులో సమాధానం ఇవ్వండి.",
}

# Unicode ranges for robust native script detection
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")
TELUGU_REGEX = re.compile(r"[\u0C00-\u0C7F]")


def detect_language(text: str) -> str:
    """Detect language of the given text using script analysis and langdetect.
    
    Returns an ISO 639-1 code ('en', 'hi', 'te').
    Falls back gracefully to 'en' on any ambiguity or exception.
    """
    if not text or not text.strip():
        return "en"
    
    clean_text = text.strip()
    
    # 1. First check script characters directly (fast & 100% reliable for native scripts)
    if TELUGU_REGEX.search(clean_text):
        return "te"
    if DEVANAGARI_REGEX.search(clean_text):
        return "hi"
    
    # 2. Use langdetect for Romanized/Latin characters or other contexts
    try:
        from langdetect import detect, DetectorFactory
        # Set seed for deterministic detection results
        DetectorFactory.seed = 0
        detected = detect(clean_text)
        
        if detected in ("hi", "mr", "ne"):
            return "hi"
        elif detected == "te":
            return "te"
        elif detected == "en":
            return "en"
        else:
            logger.debug("Detected code '%s' not in primary supported list, defaulting to 'en'", detected)
            return "en"
    except Exception as e:
        logger.warning("Language detection failed for text snippet: %s. Defaulting to 'en'. Error: %s", clean_text[:50], e)
        return "en"


def translate_text(text: str, target_language: str, source_language: str = "auto") -> str:
    """Translate text using deep-translator GoogleTranslator.
    
    Falls back to original text if translation fails or if target equals source.
    Logs errors without raising exceptions.
    
    Args:
        text: The source text to translate.
        target_language: Target language code ('en', 'hi', 'te').
        source_language: Source language code or 'auto'.
        
    Returns:
        Translated string or original string if translation is unavailable.
    """
    if not text or not text.strip():
        return text
    
    target_code = target_language.lower().strip()
    if target_code not in LANGUAGE_NAMES:
        target_code = "en"
        
    if source_language.lower() == target_code:
        return text
        
    try:
        from deep_translator import GoogleTranslator
        
        translator = GoogleTranslator(source=source_language, target=target_code)
        
        # deep-translator handles chunks up to 5000 characters
        if len(text) > 4500:
            chunks = [text[i:i + 4500] for i in range(0, len(text), 4500)]
            translated_chunks = [translator.translate(chunk) for chunk in chunks]
            return "".join(translated_chunks)
        
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as err:
        logger.warning(
            "Translation from '%s' to '%s' failed. Preserving original text. Error: %s",
            source_language, target_code, err
        )
        return text
