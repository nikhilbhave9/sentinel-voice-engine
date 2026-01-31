import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- REQUIRED ---
    google_api_key: str = Field(
        ..., 
        description="Google Gemini API Key"
    )

    # --- Optional: App settings ---
    app_title: str = Field(
        default="Sentinel Insurance Agent",
        description="Application title"
    )

    # --- Optional: LLM settings ---
    model_name: str = Field(
        default="gemini-2.5-flash-lite",
        description="LLM model to use"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0, le=2.0,  # Must be between 0 and 2
        description="Creativity parameter (0=focused, 2=random)"
    )
    
    max_tokens: int = Field(
        default=80,  # ~60 words = 2 sentences for voice
        ge=1, 
        le=8192,
        description="Max response length"
    )

    model_config = SettingsConfigDict(
        env_file=".env",              # Read from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,         # GOOGLE_API_KEY = google_api_key
        extra="ignore"                # Ignore unknown env vars
    )

# Global singleton instance (loaded once, reused everywhere)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (loads once, then cached)
    """
    global _settings
    if _settings is None:
        _settings = Settings()  # This reads .env file automatically
    return _settings