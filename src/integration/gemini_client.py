import os
import time
from typing import List, Dict, Optional, Any
import google.genai as genai
from google.genai.types import GenerateContentConfig
from google.api_core import exceptions as google_exceptions


class GeminiAPIError(Exception):
    """Custom exception for Gemini API related errors."""
    pass


class GeminiClient:
    """
    Client for interacting with Google Gemini 1.5 Flash LLM.
    
    Handles conversation context management, error handling, and retry logic
    for generating AI responses in the insurance agent.
    """
    
    def __init__(self):
        self.client = None
        self.model = None
        self.model_name = "gemini-1.5-flash"
        self.temperature = 0.7
        self.max_tokens = 1024
        self.timeout_seconds = 30
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff delays in seconds
    
    def initialize_client(self, api_key: Optional[str] = None) -> None:
        try:
            if api_key is None:
                api_key = os.getenv('GOOGLE_API_KEY')
            
            if not api_key:
                raise GeminiAPIError(
                    "Google API key is required. Set GOOGLE_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            
            # Initialize the client
            self.client = genai.Client(api_key=api_key)
            
            # Configure generation settings
            self.generation_config = GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                top_p=0.8,
                top_k=40
            )
            
            self.model = True  # Flag to indicate initialization
            
            # Test the connection with a simple request
            self._test_connection()
            
        except Exception as e:
            if isinstance(e, GeminiAPIError):
                raise
            raise GeminiAPIError(f"Failed to initialize Gemini client: {str(e)}")
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response using the Gemini model.
        
        Args:
            messages: List of conversation messages with 'role' and 'content' keys. Role should be 'user' or 'model' (model = agent).
            system_prompt: Optional system prompt to guide the conversation.
            
        Returns:
            Generated response text from the model.
        """
        if self.model is None:
            raise GeminiAPIError("Gemini client not initialized. Call initialize_client() first.")
        
        if not messages:
            raise GeminiAPIError("Messages list cannot be empty.")
        
        # Validate message format
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                raise GeminiAPIError("Each message must be a dict with 'role' and 'content' keys.")
            if msg['role'] not in ['user', 'model']:
                raise GeminiAPIError("Message role must be 'user' or 'model'.")
        
        try:
            conversation_context = self._prepare_conversation_context(messages, system_prompt)
            response = self._generate_with_retry(conversation_context)
            
            return response
            
        except Exception as e:
            error_msg = self.handle_api_error(e)
            raise GeminiAPIError(error_msg)
    
    def handle_api_error(self, error: Exception) -> str:
        if isinstance(error, google_exceptions.ResourceExhausted):
            return "I'm currently experiencing high demand. Please try again in a moment."
        
        elif isinstance(error, google_exceptions.Unauthenticated):
            return "Authentication failed. Please check your API configuration."
        
        elif isinstance(error, google_exceptions.PermissionDenied):
            return "Access denied. Please verify your API permissions."
        
        elif isinstance(error, google_exceptions.DeadlineExceeded):
            return "Request timed out. Please try again."
        
        elif isinstance(error, google_exceptions.ServiceUnavailable):
            return "I'm temporarily unavailable. Please try again in a moment."
        
        elif isinstance(error, google_exceptions.TooManyRequests):
            return "Too many requests. Please wait a moment before trying again."
        
        elif "safety" in str(error).lower():
            return "I cannot provide a response to that request. Please try rephrasing your question."
        
        else:
            # Generic error message for unknown errors
            return "I encountered an unexpected issue. Please try again or contact support if the problem persists."
    
    def _test_connection(self) -> None:
        try:
            test_content = "Hello"
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=test_content,
                config=self.generation_config
            )
            if not response or not response.text:
                raise GeminiAPIError("Connection test failed: No response received")
        except Exception as e:
            raise GeminiAPIError(f"Connection test failed: {str(e)}")
    
    def _prepare_conversation_context(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Prepare the conversation context for the Gemini model.
        
        Args:
            messages: List of conversation messages.
            system_prompt: Optional system prompt.
            
        Returns:
            Formatted conversation context string.
        """
        context_parts = []
        
        # Add system prompt if provided
        if system_prompt:
            context_parts.append(f"System: {system_prompt}\n")
        
        # Add conversation history
        for msg in messages:
            role = "Human" if msg['role'] == 'user' else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        # Add prompt for the next response
        context_parts.append("Assistant:")
        
        return "\n".join(context_parts)
    
    def _generate_with_retry(self, conversation_context: str) -> str:
        """
        Generate response with retry logic for handling transient failures.
        
        Args:
            conversation_context: Formatted conversation context.
            
        Returns:
            Generated response text.
            
        Raises:
            Exception: If all retry attempts fail.
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=conversation_context,
                    config=self.generation_config
                )
                
                if response and response.text:
                    return response.text.strip()
                else:
                    raise GeminiAPIError("Empty response received from model")
                    
            except Exception as e:
                last_exception = e
                
                # Check if this is a retryable error
                if not self._is_retryable_error(e):
                    raise e
                
                # If not the last attempt, wait before retrying
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    time.sleep(delay)
        
        # If we get here, all retries failed
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        retryable_errors = (
            google_exceptions.DeadlineExceeded,
            google_exceptions.ServiceUnavailable,
            google_exceptions.InternalServerError,
            google_exceptions.TooManyRequests,
        )
        
        return isinstance(error, retryable_errors)
    
    def is_initialized(self) -> bool:
        return self.client is not None and self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "initialized": self.is_initialized()
        }