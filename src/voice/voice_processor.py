"""
Voice Processor for Sentinel Insurance Agent

This module provides a Pipecat processor that bridges the voice pipeline
to the existing Sentinel agent logic. It enforces voice-specific constraints
like the 2-sentence maximum while maintaining full compatibility with the
existing conversation flow manager.

Pipeline flow:
    Microphone → Whisper STT → [Voice Processor] → XTTS TTS → Speaker
                                      ↓
                              process_message()
                              (existing agent logic)
"""

import logging
import re
from typing import Optional

from pipecat.processors.frame_processor import FrameProcessor
from pipecat.frames.frames import TextFrame, Frame

from src.core.conversation_flow_manager import process_message
from src.core.models import ConversationStateData
from src.core.config import get_settings


logger = logging.getLogger(__name__)


class SentinelVoiceProcessor(FrameProcessor):
    """
    Pipecat processor that bridges voice pipeline to Sentinel agent logic.
    
    This processor:
    1. Receives TextFrame from Whisper STT with user's transcribed speech
    2. Calls existing process_message() with conversation state
    3. Enforces 2-sentence maximum constraint on responses
    4. Returns TextFrame for XTTS TTS to synthesize
    
    The processor maintains conversation state and ensures voice responses
    are concise while preserving all existing business logic.
    """
    
    def __init__(self, conversation_state: ConversationStateData):
        """
        Initialize the voice processor.
        
        Args:
            conversation_state: Current conversation state to maintain context
        """
        super().__init__()
        self.conversation_state = conversation_state
        self.config = get_settings()
        self.max_sentences = self.config.voice_max_sentences
        
        logger.info(
            f"SentinelVoiceProcessor initialized with max_sentences={self.max_sentences}"
        )
    
    async def process_frame(self, frame: Frame) -> Frame:
        """
        Process incoming frames from the voice pipeline.
        
        Args:
            frame: Input frame (typically TextFrame from STT)
        
        Returns:
            Output frame (TextFrame for TTS or pass-through)
        """
        # Only process TextFrames (transcribed speech)
        if not isinstance(frame, TextFrame):
            return frame
        
        try:
            user_text = frame.text
            logger.info(f"Voice input received: {user_text}")
            
            # Call existing agent logic (no changes to core functionality)
            result = process_message(user_text, self.conversation_state)
            response = result.get("response", "")
            
            if not response:
                logger.warning("Empty response from process_message")
                response = "I apologize, I didn't catch that. Could you please repeat?"
            
            # Enforce sentence limit for voice output
            limited_response = self._limit_sentences(response)
            
            logger.info(f"Voice output generated: {limited_response}")
            
            # Return text frame for TTS
            return TextFrame(text=limited_response)
            
        except Exception as e:
            logger.error(f"Error processing voice frame: {e}", exc_info=True)
            # Return error message as TextFrame
            error_response = "I'm having trouble processing that. Could you try again?"
            return TextFrame(text=error_response)
    
    def _limit_sentences(self, text: str) -> str:
        """
        Enforce maximum sentence limit for voice responses.
        
        This method splits the response into sentences and takes only the
        first N sentences (configured via voice_max_sentences). This ensures
        voice responses are concise and don't overwhelm the user.
        
        Args:
            text: Original response text from agent
        
        Returns:
            Limited response text (max N sentences)
        """
        if not text or not text.strip():
            return ""
        
        # Split into sentences using common sentence terminators
        # Handles: "Hello. How are you? I'm fine!"
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        # Remove empty sentences
        sentences = [s for s in sentences if s.strip()]
        
        if not sentences:
            return text
        
        # Take only first N sentences
        limited = sentences[:self.max_sentences]
        result = ' '.join(limited)
        
        # Log if truncation occurred
        if len(sentences) > self.max_sentences:
            logger.info(
                f"Response truncated from {len(sentences)} to "
                f"{self.max_sentences} sentences"
            )
            logger.debug(f"Original: {text}")
            logger.debug(f"Limited: {result}")
        
        return result
