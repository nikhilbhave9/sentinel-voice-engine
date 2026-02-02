"""
Simplified Gemini AI integration.
Handles API communication, response processing, and basic error handling.
"""

import logging
import time
from typing import Dict, Any, Optional, List
import google.genai as genai
from src.core.config import get_settings
from src.core.tools import SENTINEL_TOOL_MAP

logger = logging.getLogger(__name__)

# Global client instance
_client = None
_last_request_time = 0
_request_count = 0
_daily_request_count = 0
_daily_reset_time = 0

# Rate limiting constants
REQUESTS_PER_MINUTE = 10  # gemini-2.5-flash-lite limit
REQUESTS_PER_DAY = 1000   # Conservative daily limit
MIN_REQUEST_INTERVAL = 60 / REQUESTS_PER_MINUTE  # 6 seconds between requests


def _initialize_client():
    global _client
    if _client is None:
        config_settings = get_settings()
        api_key = config_settings.google_api_key
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        _client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized successfully")


def _check_rate_limits():
    global _last_request_time, _request_count, _daily_request_count, _daily_reset_time
    
    current_time = time.time()
    
    # Reset daily counter if it's a new day
    if current_time - _daily_reset_time > 86400:  # 24 hours
        _daily_request_count = 0
        _daily_reset_time = current_time
    
    # Check daily limit
    if _daily_request_count >= REQUESTS_PER_DAY:
        raise Exception("Daily API request limit exceeded. Please try again tomorrow.")
    
    # Check per-minute rate limit
    time_since_last_request = current_time - _last_request_time
    if time_since_last_request < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - time_since_last_request
        logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    _last_request_time = time.time()
    _request_count += 1
    _daily_request_count += 1


def generate_response(prompt: str, context: str = "", conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Main API call to Gemini
    
    Args:
        prompt: The user's message or system prompt
        context: Additional context for the conversation
        conversation_history: List of previous messages in format [{"role": "user/model", "content": "..."}]
    
    Returns:
        Generated response from Gemini
    """
    try:
        _initialize_client()
        _check_rate_limits()
        
        # 1. Prepare history (Ensure we use 'user' and 'model' roles)
        contents = []
        if conversation_history:
            for msg in conversation_history:
                role = "model" if msg.get("role") in ["assistant", "model"] else "user"
                text_content = ""
                if "content" in msg:
                    text_content = msg["content"]
                elif "parts" in msg and isinstance(msg["parts"], list):
                    text_content = msg["parts"][0].get("text", "")
                if text_content:
                    contents.append({
                        "role": role,
                        "parts": [{"text": text_content}]
                    })

        # 2. Append current turn with context by wrapping the user prompt with the injected state context
        user_input = f"CONTEXT:\n{context}\n\nUSER_MESSAGE: {prompt}" if context else prompt
        contents.append({"role": "user", "parts": [{"text": user_input}]})

        config_settings = get_settings()

        # 3. Call Gemini by passing the functions directly from SENTINEL_TOOL_MAP.values()
        response = _client.models.generate_content(
            model=config_settings.model_name,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                tools=list(SENTINEL_TOOL_MAP.values()),
                automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(disable=False),
                temperature=config_settings.temperature,
                max_output_tokens=config_settings.max_tokens,
                # System instructions should ideally be in the config if not in history
                system_instruction="You are Sentinel, a high-end insurance agent assistant."
            )
        )
        
        # 4. Extract text safely
        if response.text:
            return format_response(response.text)
        
        # Fallback if the model only called a tool but didn't give a text summary
        return "Action completed successfully. How else can I help?"

    except Exception as e:
        return handle_api_error(e)


def format_response(raw_response: str) -> str:
    """
    Process and format API response
    
    Args:
        raw_response: Raw response text from Gemini
    
    Returns:
        Formatted response text
    """
    if not raw_response:
        return "I apologize, but I didn't receive a proper response. Could you please try again?"
    
    # Basic formatting - remove excessive whitespace and ensure proper line breaks
    formatted = raw_response.strip()
    
    # # Ensure response isn't too long (truncate if necessary)
    # max_length = 2000
    # if len(formatted) > max_length:
    #     formatted = formatted[:max_length] + "..."
    #     logger.warning(f"Response truncated from {len(raw_response)} to {max_length} characters")
    
    return formatted


def handle_api_error(error: Exception) -> str:
    """
    Basic error handling for API failures
    
    Args:
        error: The exception that occurred
    
    Returns:
        User-friendly error message
    """
    error_str = str(error).lower()
    
    # Handle specific error types
    if "429" in error_str or "resource exhausted" in error_str or "quota exceeded" in error_str:
        logger.warning(f"Rate limit exceeded: {error}")
        return "I'm receiving too many requests right now. Please wait a moment and try again."
    
    elif "401" in error_str or "unauthorized" in error_str or "api key" in error_str:
        logger.error(f"Authentication error: {error}")
        return "There's an issue with the API configuration. Please check your settings."
    
    elif "400" in error_str or "bad request" in error_str:
        logger.error(f"Bad request error: {error}")
        return "I couldn't process your request. Could you please rephrase it?"
    
    elif "timeout" in error_str or "connection" in error_str:
        logger.error(f"Connection error: {error}")
        return "I'm having trouble connecting right now. Please try again in a moment."
    
    else:
        logger.error(f"Unexpected Gemini API error: {error}")
        return "Sorry, I'm having trouble processing your request right now. Please try again."


def get_client_info() -> Dict[str, Any]:
    """
    Get information about the current client configuration
    
    Returns:
        Dictionary with client configuration details
    """
    return {
        "model_name": "gemini-2.5-flash-lite",
        "temperature": 0.7,
        "max_tokens": 1024,
        "initialized": _client is not None,
        "requests_per_minute_limit": REQUESTS_PER_MINUTE,
        "requests_per_day_limit": REQUESTS_PER_DAY,
        "daily_requests_made": _daily_request_count
    }