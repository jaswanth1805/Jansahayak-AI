"""Application Configuration Module.

This module defines configuration settings for the JanSahayak AI backend
using Pydantic BaseSettings, loading values from environment variables or a .env file.
"""

from functools import lru_cache
from typing import List
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """JanSahayak backend application settings.
    
    Attributes match environment variables defined in .env or .env.example.
    Default values provide a working local configuration out-of-the-box.
    """
    
    # OpenAI API Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Ready-made LLM Providers (Gemini, Groq, OpenRouter)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-2.0-flash-exp:free"
    
    # Server Host and Port
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    PORT: int = 8000
    DEBUG: bool = False
    
    # Allowed CORS Origins (comma-separated string or list)
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # File Upload Restrictions
    MAX_UPLOAD_SIZE_MB: int = Field(default=20, ge=1, le=100)
    MAX_PDF_PAGES: int = Field(default=200, ge=1, le=2000)
    MAX_EXTRACTED_TEXT_CHARS: int = Field(default=1_000_000, ge=10_000, le=10_000_000)
    DOCUMENT_RETENTION_HOURS: int = Field(default=24, ge=1, le=8760)
    UPLOAD_DIR: str = "./uploads"
    
    # Local ChromaDB Vector Store Path
    CHROMADB_PATH: str = "./chroma_db"
    
    # Audio Cache Directory for Text-to-Speech
    AUDIO_CACHE_DIR: str = "./audio_cache"
    
    # Government Source API Base URLs and Keys
    MYSCHEME_API_BASE: str = "https://api.myscheme.gov.in"
    DATA_GOV_API_KEY: str = ""
    
    # Pydantic v2 Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS_ORIGINS string into a clean list of origins."""
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Convert MAX_UPLOAD_SIZE_MB into bytes for easy validation."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings.
    
    Using lru_cache prevents re-reading environment variables or .env on every request.
    """
    return Settings()
