import logging
import os
import tempfile
import time
import re
import wave
import numpy as np
from typing import Optional
from pathlib import Path

import src.voice.tts_patch

from faster_whisper import WhisperModel
from piper import PiperVoice
import soundfile as sf

from src.core.conversation_flow_manager import process_message
from src.core.models import ConversationStateData
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class StreamlitVoiceHandler:
    """
    Fast voice handler using Piper TTS.
    """
    
    def __init__(self, conversation_state: ConversationStateData):
        self.conversation_state = conversation_state
        self.config = get_settings()
        
        # Models (lazy loaded)
        self._stt_model: Optional[WhisperModel] = None
        self._tts_model: Optional[PiperVoice] = None
        
        # Settings
        self.max_sentences = self.config.voice_max_sentences
        self.sample_rate = 22050  # Piper default
        
        logger.info("StreamlitVoiceHandler initialized (Piper version)")
    
    @property
    def stt_model(self) -> WhisperModel:
        """Lazy load Whisper STT"""
        if self._stt_model is None:
            logger.info("Loading Faster-Whisper (tiny)...")
            
            self._stt_model = WhisperModel(
                "tiny",  # Fastest model
                device="cpu",
                compute_type="int8",
                num_workers=1
            )
            logger.info("Whisper loaded")
        
        return self._stt_model
    
    @property
    def tts_model(self) -> PiperVoice:
        """Lazy load Piper TTS from local files"""
        if self._tts_model is None:
            # Path(__file__).parent points to the 'voice/' directory
            voice_dir = Path(__file__).parent
            
            model_path = voice_dir / "en_US-lessac-medium.onnx"
            config_path = voice_dir / "en_US-lessac-medium.onnx.json"
            
            logger.info(f"Loading Piper TTS from: {model_path}")
            
            if model_path.exists() and config_path.exists():
                try:
                    # Convert Path objects to strings for PiperVoice.load
                    self._tts_model = PiperVoice.load(str(model_path), config_path=str(config_path))
                    logger.info(f"Piper loaded successfully")
                except Exception as e:
                    logger.error(f"Error loading Piper: {e}")
                    raise
            else:
                logger.error(f"FILES NOT FOUND! Checked: {model_path}")
                raise FileNotFoundError(f"Missing {model_path.name} in {voice_dir}")
                
        return self._tts_model

    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """Fast transcription with Whisper"""
        try:
            logger.info(f"Transcribing: {audio_file_path}")
            
            segments, info = self.stt_model.transcribe(
                audio_file_path,
                beam_size=1,  # Fast beam search
                language="en",
                vad_filter=True,
                vad_parameters=dict(
                    threshold=0.5,
                    min_silence_duration_ms=500
                )
            )
            
            transcription = " ".join([segment.text for segment in segments])
            transcription = transcription.strip()
            
            logger.info(f"Transcribed: {transcription}")
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            raise
    
    def synthesize_speech(self, text: str, output_path: str) -> str:
        """
        Synthesize speech using Piper TTS and save to a WAV file.
        
        Args:
            text: Text to synthesize
            output_path: Output WAV file path

        Returns:
            Path to generated audio
        """
        # Clean and limit text
        logger.info(f"Full text: {text}")
        limited_text = self._limit_sentences(text)
        logger.info(f"Limited text: {limited_text}")

        # Test
        limited_text = text

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        try:
            with wave.open(output_path, "wb") as wav_file:
                first_chunk = True
                
                # Iterate through Piper's generator
                for chunk in self.tts_model.synthesize(limited_text):
                    # Dynamically set WAV header parameters from the first chunk
                    if first_chunk:
                        wav_file.setnchannels(chunk.sample_channels)
                        wav_file.setsampwidth(chunk.sample_width)
                        wav_file.setframerate(chunk.sample_rate)
                        first_chunk = False
                    
                    # Use the specific bytes attr
                    wav_file.writeframes(chunk.audio_int16_bytes)

            # Verify file integrity
            size = os.path.getsize(output_path)
            logger.info(f"Audio synthesis complete. Size: {size} bytes")

            # A valid WAV header is 44 bytes; anything less or equal is empty
            if size <= 44:
                raise RuntimeError("Piper produced an empty or invalid audio file")

        except Exception as e:
            logger.error(f"Failed to synthesize speech: {str(e)}")
            raise e

        return output_path
    
    def _limit_sentences(self, text: str) -> str:
        """
        ENFORCE max_sentences limit (CRITICAL for voice)
        
        Args:
            text: Original text
        
        Returns:
            Text limited to max_sentences
        """
        if not text or not text.strip():
            return ""
        
        # Split on sentence terminators
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s for s in sentences if s.strip()]
        
        if not sentences:
            return text
        
        # ENFORCE limit
        limited = sentences[:self.max_sentences]
        result = ' '.join(limited)
        
        if len(sentences) > self.max_sentences:
            logger.warning(
                f"⚠️ TRUNCATED: {len(sentences)} → {self.max_sentences} sentences"
            )
            logger.debug(f"Original: {text}")
            logger.debug(f"Limited: {result}")
        
        return result