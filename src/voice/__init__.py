"""
Voice capabilities module for Sentinel Insurance Agent.

This module provides voice interaction capabilities using:
- Faster-Whisper for speech-to-text
- XTTS for text-to-speech
- Pipecat framework for pipeline orchestration
"""

__version__ = "1.0.0"

# Apply PyTorch compatibility patch for TTS library
# This must be imported before TTS.api to ensure torch.load uses weights_only=False
from src.voice import tts_patch
