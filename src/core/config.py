"""
Simplified configuration management.
Handles environment variables and basic validation.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    # Load environment variables from .env file
    load_dotenv()
    
    config = {
        "gemini_api_key": os.getenv("GOOGLE_API_KEY"),
        "app_title": os.getenv("APP_TITLE", "Insurance Agent"),
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true"
    }
    
    return config


def get_api_key() -> str:
    """Retrieve Gemini API key from environment"""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    return api_key


def validate_required_config() -> bool:
    """Basic configuration validation"""
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return False
    
    return True