"""
Latency tracking infrastructure for monitoring performance metrics.

This module provides tools for tracking processing latency across different
stages of the voice pipeline (STT, LLM, TTS) to enable real-time performance
monitoring in the command center UI.
"""

from dataclasses import dataclass
from typing import Optional
import time
from contextlib import contextmanager


@dataclass
class LatencyMetrics:
    """
    Track latency for different processing stages.
    
    This dataclass stores performance metrics for the voice pipeline,
    including STT (Speech-to-Text), LLM (Language Model), and TTS
    (Text-to-Speech) processing times.
    
    Attributes:
        stt_latency_ms: Speech-to-text processing time in milliseconds
        llm_latency_ms: Language model response generation time in milliseconds
        tts_latency_ms: Text-to-speech synthesis time in milliseconds
        total_latency_ms: Total end-to-end processing time in milliseconds
        token_count: Number of tokens used in LLM processing
        model_name: Name of the LLM model being used
    """
    stt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    token_count: int = 0
    model_name: str = ""
    
    def __post_init__(self):
        """Calculate total latency after initialization."""
        self._update_total_latency()
    
    def to_dict(self) -> dict:
        """
        Convert metrics to dictionary format for easy serialization.
        
        Returns:
            Dictionary with rounded latency values and metadata suitable
            for display in the UI or storage in session state.
        """
        return {
            "stt_ms": round(self.stt_latency_ms, 2),
            "llm_ms": round(self.llm_latency_ms, 2),
            "tts_ms": round(self.tts_latency_ms, 2),
            "total_ms": round(self.total_latency_ms, 2),
            "tokens": self.token_count,
            "model": self.model_name
        }
    
    def update_stt_latency(self, latency_ms: float) -> None:
        """
        Update STT latency and recalculate total latency.
        
        Args:
            latency_ms: STT processing time in milliseconds
        """
        self.stt_latency_ms = latency_ms
        self._update_total_latency()
    
    def update_llm_latency(self, latency_ms: float, token_count: Optional[int] = None, 
                          model_name: Optional[str] = None) -> None:
        """
        Update LLM latency and optionally token count and model name.
        
        Args:
            latency_ms: LLM processing time in milliseconds
            token_count: Number of tokens used (optional)
            model_name: Name of the model used (optional)
        """
        self.llm_latency_ms = latency_ms
        if token_count is not None:
            self.token_count = token_count
        if model_name is not None:
            self.model_name = model_name
        self._update_total_latency()
    
    def update_tts_latency(self, latency_ms: float) -> None:
        """
        Update TTS latency and recalculate total latency.
        
        Args:
            latency_ms: TTS processing time in milliseconds
        """
        self.tts_latency_ms = latency_ms
        self._update_total_latency()
    
    def _update_total_latency(self) -> None:
        """Recalculate total latency from individual components."""
        self.total_latency_ms = (
            self.stt_latency_ms + 
            self.llm_latency_ms + 
            self.tts_latency_ms
        )
    
    def reset(self) -> None:
        """Reset all metrics to default values."""
        self.stt_latency_ms = 0.0
        self.llm_latency_ms = 0.0
        self.tts_latency_ms = 0.0
        self.total_latency_ms = 0.0
        self.token_count = 0
        self.model_name = ""


@contextmanager
def track_latency(metric_name: str = "operation"):
    """
    Context manager for tracking operation latency.
    
    This context manager measures the elapsed time of an operation
    and yields the elapsed time in milliseconds when the context exits.
    
    Usage:
        with track_latency("STT") as timer:
            # Perform STT operation
            result = transcribe_audio(audio_data)
        elapsed_ms = timer()
    
    Args:
        metric_name: Name of the operation being tracked (for logging)
    
    Yields:
        A callable that returns the elapsed time in milliseconds
    """
    start_time = time.time()
    elapsed_ms = [0.0]  # Use list to allow modification in nested function
    
    def get_elapsed():
        """Get the elapsed time in milliseconds."""
        return elapsed_ms[0]
    
    try:
        yield get_elapsed
    finally:
        elapsed_ms[0] = (time.time() - start_time) * 1000  # Convert to ms


class LatencyTracker:
    """
    Helper class for tracking latency across multiple operations.
    
    This class provides a convenient interface for tracking latency
    with automatic storage and retrieval of measurements.
    """
    
    def __init__(self):
        """Initialize the latency tracker."""
        self.metrics = LatencyMetrics()
    
    def track_stt(self, latency_ms: float) -> None:
        """Track STT latency."""
        self.metrics.update_stt_latency(latency_ms)
    
    def track_llm(self, latency_ms: float, token_count: Optional[int] = None,
                  model_name: Optional[str] = None) -> None:
        """Track LLM latency with optional metadata."""
        self.metrics.update_llm_latency(latency_ms, token_count, model_name)
    
    def track_tts(self, latency_ms: float) -> None:
        """Track TTS latency."""
        self.metrics.update_tts_latency(latency_ms)
    
    def get_metrics(self) -> LatencyMetrics:
        """Get the current metrics."""
        return self.metrics
    
    def get_metrics_dict(self) -> dict:
        """Get metrics as a dictionary."""
        return self.metrics.to_dict()
    
    def reset(self) -> None:
        """Reset all tracked metrics."""
        self.metrics.reset()
