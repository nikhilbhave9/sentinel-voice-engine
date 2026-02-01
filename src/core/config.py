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

    # --- Optional: Voice STT Configuration ---
    voice_stt_model: str = Field(
        default="base",
        description="Faster-Whisper model size (tiny/base/small/medium/large)"
    )
    
    voice_stt_device: str = Field(
        default="cpu",
        description="Device for STT (cpu/cuda)"
    )
    
    voice_stt_compute_type: str = Field(
        default="int8",
        description="Compute type for STT (int8/float16/float32)"
    )

    # --- Optional: Voice TTS Configuration ---
    voice_tts_model: str = Field(
        default="tts_models/multilingual/multi-dataset/xtts_v2",
        description="XTTS model path"
    )
    
    voice_tts_language: str = Field(
        default="en",
        description="TTS language code"
    )
    
    voice_tts_speed: float = Field(
        default=1.0,
        ge=0.5, le=2.0,
        description="Speech speed multiplier"
    )

    # --- Optional: Voice Pipeline Configuration ---
    voice_silence_threshold: float = Field(
        default=0.5,
        ge=0.0, le=1.0,
        description="Silence detection threshold (0-1)"
    )
    
    voice_silence_duration: float = Field(
        default=0.8,
        ge=0.1, le=3.0,
        description="Silence duration in seconds before processing"
    )
    
    voice_max_sentences: int = Field(
        default=2,
        ge=1, le=5,
        description="Maximum sentences per response"
    )
    
    voice_enabled: bool = Field(
        default=True,
        description="Enable/disable voice features"
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