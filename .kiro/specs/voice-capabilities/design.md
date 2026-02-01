# Voice Capabilities Design Document

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit UI Layer                          │
│  ┌──────────────┐              ┌──────────────┐                │
│  │  Text Chat   │              │ Voice Call   │                │
│  │  Interface   │              │  Interface   │                │
│  └──────┬───────┘              └──────┬───────┘                │
└─────────┼──────────────────────────────┼──────────────────────┘
          │                              │
          │         ┌────────────────────┘
          │         │
          ▼         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Conversation Flow Manager                          │
│              (existing - no changes)                            │
│  • Intent Detection    • State Transitions                      │
│  • Info Extraction     • Context Building                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Gemini LLM Client                            │
│                    (existing - no changes)                      │
└─────────────────────────────────────────────────────────────────┘

Voice Pipeline (NEW):
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   Mic    │───▶│ Whisper  │───▶│  Voice   │───▶│   XTTS   │
│  Input   │    │   STT    │    │Processor │    │   TTS    │
└──────────┘    └──────────┘    └────┬─────┘    └──────┬───┘
                                     │                  │
                                     ▼                  ▼
                            ┌─────────────────┐  ┌──────────┐
                            │ Flow Manager    │  │ Speaker  │
                            │ process_message │  │  Output  │
                            └─────────────────┘  └──────────┘
```

### 1.2 Component Responsibilities

**Existing Components (No Changes):**
- `conversation_flow_manager.py`: Intent detection, state management, info extraction
- `gemini_client.py`: LLM API calls and response generation
- `models.py`: Data structures for conversation state
- `prompts.py`: System prompts and patterns

**New Components:**
- `voice/voice_processor.py`: Pipecat processor bridging voice to agent logic
- `voice/pipecat_handler.py`: Pipeline orchestration and lifecycle management
- `src/core/config.py`: Extended with voice configuration
- `app.py`: Extended with voice UI controls



## 2. Voice Configuration Design

### 2.1 Extended Configuration Schema

```python
# src/core/config.py additions

class Settings(BaseSettings):
    # ... existing fields ...
    
    # Voice STT Configuration
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
    
    # Voice TTS Configuration
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
    
    # Voice Pipeline Configuration
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
```

### 2.2 Environment Variables

```bash
# .env additions for voice configuration

# STT Settings
VOICE_STT_MODEL=base
VOICE_STT_DEVICE=cpu
VOICE_STT_COMPUTE_TYPE=int8

# TTS Settings
VOICE_TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
VOICE_TTS_LANGUAGE=en
VOICE_TTS_SPEED=1.0

# Pipeline Settings
VOICE_SILENCE_THRESHOLD=0.5
VOICE_SILENCE_DURATION=0.8
VOICE_MAX_SENTENCES=2
VOICE_ENABLED=true
```



## 3. Voice Processor Design

### 3.1 Voice Processor Class

```python
# voice/voice_processor.py

from pipecat.processors.frame_processor import FrameProcessor
from pipecat.frames.frames import TextFrame, Frame
from src.core.conversation_flow_manager import process_message
from src.core.models import ConversationStateData
from src.core.config import get_settings
import logging
import re

class SentinelVoiceProcessor(FrameProcessor):
    """
    Pipecat processor that bridges voice pipeline to Sentinel agent logic.
    
    Pipeline flow:
    1. Receives TextFrame from Whisper STT
    2. Calls existing process_message() with conversation state
    3. Enforces 2-sentence maximum constraint
    4. Outputs TextFrame for XTTS TTS
    """
    
    def __init__(self, conversation_state: ConversationStateData):
        super().__init__()
        self.conversation_state = conversation_state
        self.config = get_settings()
        self.logger = logging.getLogger(__name__)
        self.max_sentences = self.config.voice_max_sentences
    
    async def process_frame(self, frame: Frame) -> Frame:
        """Process incoming frames from STT"""
        if isinstance(frame, TextFrame):
            user_text = frame.text
            self.logger.info(f"Voice input: {user_text}")
            
            # Call existing agent logic
            result = process_message(user_text, self.conversation_state)
            response = result.get("response", "")
            
            # Enforce sentence limit
            limited_response = self._limit_sentences(response)
            
            self.logger.info(f"Voice output: {limited_response}")
            
            # Return text frame for TTS
            return TextFrame(text=limited_response)
        
        # Pass through other frame types
        return frame
    
    def _limit_sentences(self, text: str) -> str:
        """Enforce maximum sentence limit for voice responses"""
        if not text:
            return ""
        
        # Split into sentences (handle ., !, ?)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        # Take only first N sentences
        limited = sentences[:self.max_sentences]
        result = ' '.join(limited)
        
        if len(sentences) > self.max_sentences:
            self.logger.info(
                f"Truncated response from {len(sentences)} to "
                f"{self.max_sentences} sentences"
            )
        
        return result
```

### 3.2 Key Design Decisions

**Why Pipecat Processor?**
- Integrates seamlessly with Pipecat's frame-based architecture
- Handles async processing naturally
- Easy to insert into STT → TTS pipeline

**Why No Changes to process_message()?**
- Maintains existing business logic integrity
- Sentence limiting happens at voice layer only
- Text interface remains unaffected

**Sentence Limiting Strategy:**
- Applied after LLM generation (not in prompt)
- Uses regex to split on sentence boundaries
- Logs truncation for monitoring
- Configurable via `voice_max_sentences` setting



## 4. Pipecat Pipeline Handler Design

### 4.1 Pipeline Handler Class

```python
# voice/pipecat_handler.py

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.whisper import WhisperSTTService
from pipecat.services.xtts import XTTSService
from pipecat.transports.local_audio import LocalAudioTransport
from voice.voice_processor import SentinelVoiceProcessor
from src.core.models import ConversationStateData
from src.core.config import get_settings
import logging
import asyncio

class VoicePipelineHandler:
    """
    Orchestrates the complete voice pipeline:
    Microphone → Whisper → Voice Processor → XTTS → Speaker
    """
    
    def __init__(self, conversation_state: ConversationStateData):
        self.conversation_state = conversation_state
        self.config = get_settings()
        self.logger = logging.getLogger(__name__)
        self.pipeline = None
        self.runner = None
        self.is_running = False
    
    async def initialize(self):
        """Initialize all pipeline components"""
        try:
            # 1. Audio Transport (Mic + Speaker)
            transport = LocalAudioTransport(
                input_device_name=None,  # Default mic
                output_device_name=None,  # Default speaker
                sample_rate=16000
            )
            
            # 2. Voice Activity Detection
            vad = SileroVADAnalyzer(
                threshold=self.config.voice_silence_threshold,
                min_silence_duration=self.config.voice_silence_duration
            )
            
            # 3. Speech-to-Text (Whisper)
            stt = WhisperSTTService(
                model=self.config.voice_stt_model,
                device=self.config.voice_stt_device,
                compute_type=self.config.voice_stt_compute_type
            )
            
            # 4. Voice Processor (our custom logic)
            processor = SentinelVoiceProcessor(self.conversation_state)
            
            # 5. Text-to-Speech (XTTS)
            tts = XTTSService(
                model_name=self.config.voice_tts_model,
                language=self.config.voice_tts_language,
                speed=self.config.voice_tts_speed
            )
            
            # 6. Build Pipeline
            self.pipeline = Pipeline([
                transport.input(),
                vad,
                stt,
                processor,
                tts,
                transport.output()
            ])
            
            # 7. Create Runner
            self.runner = PipelineRunner(self.pipeline)
            
            self.logger.info("Voice pipeline initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize pipeline: {e}")
            raise
    
    async def start(self):
        """Start the voice pipeline"""
        if self.is_running:
            self.logger.warning("Pipeline already running")
            return
        
        try:
            await self.initialize()
            self.is_running = True
            await self.runner.run()
            self.logger.info("Voice pipeline started")
        except Exception as e:
            self.logger.error(f"Failed to start pipeline: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the voice pipeline and cleanup resources"""
        if not self.is_running:
            return
        
        try:
            if self.runner:
                await self.runner.stop()
            
            self.is_running = False
            self.pipeline = None
            self.runner = None
            
            self.logger.info("Voice pipeline stopped")
        except Exception as e:
            self.logger.error(f"Error stopping pipeline: {e}")
            raise
    
    def get_status(self) -> dict:
        """Get current pipeline status"""
        return {
            "is_running": self.is_running,
            "has_pipeline": self.pipeline is not None,
            "config": {
                "stt_model": self.config.voice_stt_model,
                "tts_model": self.config.voice_tts_model,
                "max_sentences": self.config.voice_max_sentences
            }
        }
```

### 4.2 Pipeline Flow Details

**Frame Flow:**
```
1. Microphone captures audio → AudioFrame
2. VAD detects speech/silence → AudioFrame (filtered)
3. Whisper transcribes → TextFrame(text="user speech")
4. Voice Processor:
   - Extracts text from TextFrame
   - Calls process_message(text, state)
   - Limits response to 2 sentences
   - Returns TextFrame(text="agent response")
5. XTTS synthesizes → AudioFrame
6. Speaker plays audio
```

**Async Architecture:**
- All components run asynchronously
- Non-blocking audio I/O
- Concurrent STT/TTS processing where possible
- Graceful shutdown with resource cleanup



## 5. Streamlit Voice Interface Design

### 5.1 UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🛡️ Sentinel Insurance Agent                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐         │
│  │   Text Chat         │  │   Voice Call        │         │
│  │                     │  │                     │         │
│  │  [Chat History]     │  │  ┌───────────────┐ │         │
│  │                     │  │  │  🎤 Start Call│ │         │
│  │                     │  │  └───────────────┘ │         │
│  │                     │  │                     │         │
│  │  [Input Box]        │  │  Status: Idle       │         │
│  │                     │  │                     │         │
│  └─────────────────────┘  │  [Transcription]    │         │
│                           │  [Agent Response]   │         │
│                           │                     │         │
│                           │  ┌───────────────┐ │         │
│                           │  │  🛑 End Call  │ │         │
│                           │  └───────────────┘ │         │
│                           └─────────────────────┘         │
│                                                             │
│  Sidebar:                                                   │
│  📋 Collected Information                                   │
│  • Name: [if collected]                                     │
│  • Policy: [if collected]                                   │
│  • State: [current state]                                   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Voice Interface States

**State 1: Idle**
- Display: "Status: Ready to start call"
- Button: "🎤 Start Call" (enabled)
- Button: "🛑 End Call" (disabled)
- Transcription area: Empty
- Response area: Empty

**State 2: Initializing**
- Display: "Status: Initializing voice pipeline..."
- Button: "🎤 Start Call" (disabled)
- Button: "🛑 End Call" (disabled)
- Spinner animation

**State 3: Listening**
- Display: "Status: 🎤 Listening..."
- Button: "🎤 Start Call" (disabled)
- Button: "🛑 End Call" (enabled)
- Microphone level indicator (visual feedback)
- Transcription area: Shows live transcription

**State 4: Processing**
- Display: "Status: 🤔 Processing..."
- Button: "🎤 Start Call" (disabled)
- Button: "🛑 End Call" (enabled)
- Spinner animation
- Transcription area: Shows final user input

**State 5: Speaking**
- Display: "Status: 🔊 Speaking..."
- Button: "🎤 Start Call" (disabled)
- Button: "🛑 End Call" (enabled)
- Audio wave animation
- Response area: Shows agent response text

**State 6: Error**
- Display: "Status: ⚠️ Error - [error message]"
- Button: "🎤 Start Call" (enabled)
- Button: "🛑 End Call" (disabled)
- Error details in expandable section



### 5.3 Streamlit Integration Code Structure

```python
# app.py additions

import asyncio
from voice.pipecat_handler import VoicePipelineHandler

def main():
    # ... existing code ...
    
    # Initialize voice session state
    initialize_voice_session_state()
    
    # Create two columns: text chat and voice call
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_text_chat_interface()
    
    with col2:
        render_voice_call_interface()

def initialize_voice_session_state():
    """Initialize voice-specific session state"""
    if "voice_handler" not in st.session_state:
        st.session_state.voice_handler = None
    
    if "voice_status" not in st.session_state:
        st.session_state.voice_status = "idle"
    
    if "voice_transcription" not in st.session_state:
        st.session_state.voice_transcription = ""
    
    if "voice_response" not in st.session_state:
        st.session_state.voice_response = ""

def render_voice_call_interface():
    """Render voice call UI"""
    st.subheader("🎙️ Voice Call")
    
    # Status display
    status_color = {
        "idle": "🟢",
        "initializing": "🟡",
        "listening": "🔵",
        "processing": "🟡",
        "speaking": "🟣",
        "error": "🔴"
    }
    
    status = st.session_state.voice_status
    st.markdown(f"**Status:** {status_color.get(status, '⚪')} {status.title()}")
    
    # Control buttons
    col_start, col_end = st.columns(2)
    
    with col_start:
        start_disabled = status not in ["idle", "error"]
        if st.button("🎤 Start Call", disabled=start_disabled, key="start_call"):
            handle_start_call()
    
    with col_end:
        end_disabled = status in ["idle", "error", "initializing"]
        if st.button("🛑 End Call", disabled=end_disabled, key="end_call"):
            handle_end_call()
    
    # Transcription display
    if st.session_state.voice_transcription:
        st.markdown("**You said:**")
        st.info(st.session_state.voice_transcription)
    
    # Response display
    if st.session_state.voice_response:
        st.markdown("**Agent response:**")
        st.success(st.session_state.voice_response)

def handle_start_call():
    """Handle start call button click"""
    try:
        st.session_state.voice_status = "initializing"
        
        # Create voice handler with current conversation state
        handler = VoicePipelineHandler(st.session_state.conversation_state)
        st.session_state.voice_handler = handler
        
        # Start pipeline in background
        asyncio.run(handler.start())
        
        st.session_state.voice_status = "listening"
        st.rerun()
        
    except Exception as e:
        st.session_state.voice_status = "error"
        st.error(f"Failed to start call: {e}")
        logger.error(f"Voice call start error: {e}")

def handle_end_call():
    """Handle end call button click"""
    try:
        handler = st.session_state.voice_handler
        if handler:
            asyncio.run(handler.stop())
        
        st.session_state.voice_handler = None
        st.session_state.voice_status = "idle"
        st.rerun()
        
    except Exception as e:
        st.error(f"Error ending call: {e}")
        logger.error(f"Voice call end error: {e}")
```

### 5.4 Session State Management

**Shared State:**
- `conversation_state`: Shared between text and voice interfaces
- `messages`: Conversation history includes both text and voice
- `user_info`: Collected information from both interfaces

**Voice-Specific State:**
- `voice_handler`: VoicePipelineHandler instance
- `voice_status`: Current voice pipeline state
- `voice_transcription`: Latest user speech transcription
- `voice_response`: Latest agent voice response

**State Synchronization:**
- Voice interactions update same `conversation_state` as text
- Both interfaces see same conversation history
- User info collected via voice appears in sidebar
- Seamless switching between interfaces



## 6. Data Flow and Sequence Diagrams

### 6.1 Voice Call Initialization Sequence

```
User                Streamlit UI        VoiceHandler        Pipecat Pipeline
 │                       │                    │                    │
 │  Click "Start Call"   │                    │                    │
 ├──────────────────────>│                    │                    │
 │                       │  create handler    │                    │
 │                       ├───────────────────>│                    │
 │                       │                    │  initialize()      │
 │                       │                    ├───────────────────>│
 │                       │                    │  - setup transport │
 │                       │                    │  - load Whisper    │
 │                       │                    │  - load XTTS       │
 │                       │                    │  - build pipeline  │
 │                       │                    │<───────────────────┤
 │                       │                    │  start()           │
 │                       │                    ├───────────────────>│
 │                       │  status: listening │                    │
 │                       │<───────────────────┤                    │
 │  UI updates           │                    │                    │
 │<──────────────────────┤                    │                    │
 │  "Status: Listening"  │                    │                    │
```

### 6.2 Voice Message Processing Sequence

```
Microphone      Whisper STT    VoiceProcessor    FlowManager    Gemini    XTTS TTS    Speaker
    │               │                │                │           │          │           │
    │  audio        │                │                │           │          │           │
    ├──────────────>│                │                │           │          │           │
    │               │  transcribe    │                │           │          │           │
    │               │  "I need help" │                │           │          │           │
    │               ├───────────────>│                │           │          │           │
    │               │                │ process_message│           │          │           │
    │               │                ├───────────────>│           │          │           │
    │               │                │                │  generate │          │           │
    │               │                │                ├──────────>│          │           │
    │               │                │                │<──────────┤          │           │
    │               │                │  response      │           │          │           │
    │               │                │<───────────────┤           │          │           │
    │               │                │ limit_sentences│           │          │           │
    │               │                │ (2 max)        │           │          │           │
    │               │  "I'd be happy │                │           │          │           │
    │               │   to help."    │                │           │          │           │
    │               │<───────────────┤                │           │          │           │
    │               │                │                │           │          │           │
    │               │                │                │           │  synth   │           │
    │               │                │                │           │<─────────┤           │
    │               │                │                │           │          │  audio    │
    │               │                │                │           │          ├──────────>│
    │               │                │                │           │          │           │
```

### 6.3 Data Models

**VoiceCallState:**
```python
@dataclass
class VoiceCallState:
    """State of an active voice call"""
    is_active: bool = False
    status: str = "idle"  # idle, initializing, listening, processing, speaking, error
    start_time: Optional[datetime] = None
    last_transcription: str = ""
    last_response: str = ""
    error_message: Optional[str] = None
    latency_metrics: Dict[str, float] = field(default_factory=dict)
```

**LatencyMetrics:**
```python
@dataclass
class LatencyMetrics:
    """Track latency for performance monitoring"""
    stt_latency: float = 0.0  # Whisper transcription time
    llm_latency: float = 0.0  # Gemini response time
    tts_latency: float = 0.0  # XTTS synthesis time
    total_latency: float = 0.0  # End-to-end time
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_within_target(self, target: float = 2.0) -> bool:
        """Check if total latency meets target"""
        return self.total_latency <= target
```



## 7. Performance Optimization Strategy

### 7.1 Model Optimization

**Whisper STT:**
- Use `base` model (74M params) for balance of speed/accuracy
- CPU with `int8` quantization for 4x speedup
- Target: <1s transcription for typical utterances (5-10 seconds audio)

**XTTS TTS:**
- Use CPU inference (no GPU required)
- Streaming synthesis where possible
- Target: <1s synthesis for 2-sentence responses

**Gemini LLM:**
- Already optimized with `max_tokens=80` (~2 sentences)
- Use existing rate limiting and caching
- Target: <1s response generation

### 7.2 Concurrent Processing

```python
# Pseudo-code for concurrent processing

async def process_voice_turn():
    # 1. STT (sequential - must complete first)
    transcription = await whisper_stt.transcribe(audio)
    
    # 2. LLM + TTS preparation (can overlap)
    async with asyncio.TaskGroup() as tg:
        # Start LLM generation
        llm_task = tg.create_task(
            gemini_client.generate(transcription)
        )
        
        # Preload TTS model if needed
        tts_task = tg.create_task(
            xtts_service.prepare()
        )
    
    response = await llm_task
    limited_response = limit_sentences(response)
    
    # 3. TTS (sequential - needs response text)
    audio = await xtts_service.synthesize(limited_response)
    
    return audio
```

### 7.3 Resource Management

**Model Caching:**
- Load models once at pipeline initialization
- Keep in memory during active call
- Release on call termination
- Estimated memory: ~2GB (Whisper base + XTTS)

**Audio Buffering:**
- Use ring buffers for audio I/O
- Minimize buffer size for low latency
- Target: 50-100ms audio buffering

**Thread Pool:**
- Use asyncio for I/O-bound operations
- CPU-bound model inference in thread pool
- Prevent blocking main event loop

### 7.4 Latency Budget

```
Target: <2 seconds total

Breakdown:
- Audio capture: 0.1s (100ms buffering)
- Whisper STT: 0.8s (base model, int8)
- Gemini LLM: 0.6s (80 tokens, existing optimization)
- XTTS TTS: 0.4s (2 sentences)
- Audio playback: 0.1s (100ms buffering)
────────────────
Total: 2.0s

Optimization targets:
- STT: Use smaller model if accuracy acceptable
- LLM: Already optimized with token limit
- TTS: Use faster voice if quality acceptable
- Overlap: Concurrent processing where possible
```



## 8. Error Handling and Recovery

### 8.1 Error Categories

**Category 1: Initialization Errors**
- Microphone not found/accessible
- Audio device permission denied
- Model download/loading failure
- Insufficient memory

**Category 2: Runtime Errors**
- Audio stream interruption
- STT transcription failure
- LLM API error (existing handling)
- TTS synthesis failure
- Network connectivity issues

**Category 3: Resource Errors**
- Memory exhaustion
- CPU overload
- Disk space for model cache

### 8.2 Error Handling Strategy

```python
# voice/pipecat_handler.py error handling

class VoicePipelineHandler:
    
    async def initialize(self):
        """Initialize with comprehensive error handling"""
        try:
            # Check audio devices first
            devices = self._check_audio_devices()
            if not devices:
                raise AudioDeviceError("No audio devices found")
            
            # Load models with timeout
            await asyncio.wait_for(
                self._load_models(),
                timeout=30.0
            )
            
        except AudioDeviceError as e:
            self.logger.error(f"Audio device error: {e}")
            raise UserFacingError(
                "Microphone not found. Please check your audio settings."
            )
        
        except asyncio.TimeoutError:
            self.logger.error("Model loading timeout")
            raise UserFacingError(
                "Voice models are taking too long to load. "
                "Please check your internet connection and try again."
            )
        
        except MemoryError as e:
            self.logger.error(f"Insufficient memory: {e}")
            raise UserFacingError(
                "Not enough memory to load voice models. "
                "Please close other applications and try again."
            )
        
        except Exception as e:
            self.logger.error(f"Unexpected initialization error: {e}")
            raise UserFacingError(
                "Failed to initialize voice system. Please try again later."
            )
    
    async def _handle_runtime_error(self, error: Exception):
        """Handle errors during active call"""
        if isinstance(error, STTError):
            # Transcription failed - ask user to repeat
            await self._play_error_message(
                "I didn't catch that. Could you please repeat?"
            )
        
        elif isinstance(error, TTSError):
            # Synthesis failed - show text response
            self.logger.error(f"TTS failed: {error}")
            # Fall back to text display
            return {"mode": "text_fallback"}
        
        elif isinstance(error, AudioStreamError):
            # Audio stream interrupted - attempt recovery
            self.logger.warning(f"Audio stream error: {error}")
            await self._restart_audio_stream()
        
        else:
            # Unknown error - graceful degradation
            self.logger.error(f"Runtime error: {error}")
            await self.stop()
            raise UserFacingError(
                "Voice call encountered an error. Please try again."
            )
```

### 8.3 Graceful Degradation

**Fallback Hierarchy:**
1. **Full voice**: STT → LLM → TTS (target)
2. **Text fallback**: STT → LLM → Text display (if TTS fails)
3. **Manual input**: Text input → LLM → TTS (if STT fails)
4. **Text only**: Text input → LLM → Text display (if all voice fails)

**User Communication:**
- Clear error messages in UI
- Suggest specific actions (check mic, restart, etc.)
- Provide alternative interaction methods
- Log detailed errors for debugging



## 9. Testing Strategy

### 9.1 Unit Tests

**Test: voice_processor.py**
```python
# tests/test_voice_processor.py

def test_sentence_limiting():
    """Test that responses are limited to max sentences"""
    processor = SentinelVoiceProcessor(mock_state)
    
    # Test with 3 sentences
    input_text = "First sentence. Second sentence. Third sentence."
    result = processor._limit_sentences(input_text)
    
    sentences = result.split('. ')
    assert len(sentences) <= 2
    assert "First sentence" in result
    assert "Second sentence" in result

def test_process_message_integration():
    """Test integration with existing process_message"""
    processor = SentinelVoiceProcessor(mock_state)
    frame = TextFrame(text="I need help with my policy")
    
    result = await processor.process_frame(frame)
    
    assert isinstance(result, TextFrame)
    assert len(result.text) > 0
    assert result.text.count('.') <= 2  # Max 2 sentences
```

**Test: pipecat_handler.py**
```python
# tests/test_pipecat_handler.py

async def test_pipeline_initialization():
    """Test pipeline initializes all components"""
    handler = VoicePipelineHandler(mock_state)
    await handler.initialize()
    
    assert handler.pipeline is not None
    assert handler.runner is not None
    assert handler.is_running == False

async def test_pipeline_lifecycle():
    """Test start and stop lifecycle"""
    handler = VoicePipelineHandler(mock_state)
    
    await handler.start()
    assert handler.is_running == True
    
    await handler.stop()
    assert handler.is_running == False
    assert handler.pipeline is None
```

### 9.2 Integration Tests

**Test: End-to-End Voice Flow**
```python
# tests/integration/test_voice_e2e.py

async def test_voice_conversation_flow():
    """Test complete voice conversation"""
    # Setup
    handler = VoicePipelineHandler(ConversationStateData())
    await handler.initialize()
    
    # Simulate audio input
    test_audio = load_test_audio("hello.wav")
    
    # Process through pipeline
    result = await handler.process_audio(test_audio)
    
    # Verify
    assert result.transcription is not None
    assert result.response is not None
    assert result.audio_output is not None
    assert result.total_latency < 2.0  # Under 2 seconds
```

### 9.3 Performance Tests

**Test: Latency Measurement**
```python
# tests/performance/test_latency.py

async def test_stt_latency():
    """Measure STT latency"""
    stt = WhisperSTTService(model="base", device="cpu")
    audio = load_test_audio("5_second_speech.wav")
    
    start = time.time()
    transcription = await stt.transcribe(audio)
    latency = time.time() - start
    
    assert latency < 1.0  # Under 1 second
    assert len(transcription) > 0

async def test_end_to_end_latency():
    """Measure total pipeline latency"""
    handler = VoicePipelineHandler(mock_state)
    
    metrics = await handler.process_with_metrics(test_audio)
    
    assert metrics.stt_latency < 1.0
    assert metrics.llm_latency < 1.0
    assert metrics.tts_latency < 1.0
    assert metrics.total_latency < 2.0
```

### 9.4 Manual Testing Checklist

**Audio Device Testing:**
- [ ] Test with default microphone
- [ ] Test with external USB microphone
- [ ] Test with Bluetooth headset
- [ ] Test microphone permission denial
- [ ] Test with no microphone available

**Voice Quality Testing:**
- [ ] Test with clear speech
- [ ] Test with background noise
- [ ] Test with fast speech
- [ ] Test with slow speech
- [ ] Test with accents

**Conversation Flow Testing:**
- [ ] Test greeting flow via voice
- [ ] Test support flow via voice
- [ ] Test sales flow via voice
- [ ] Test information extraction via voice
- [ ] Test state transitions via voice

**Error Handling Testing:**
- [ ] Test with network disconnection
- [ ] Test with insufficient memory
- [ ] Test with audio stream interruption
- [ ] Test graceful degradation to text
- [ ] Test recovery after errors

**Performance Testing:**
- [ ] Measure latency over 10 conversations
- [ ] Test on minimum spec hardware
- [ ] Test with concurrent users (if applicable)
- [ ] Monitor memory usage over time
- [ ] Test model loading time



## 10. Deployment and Setup

### 10.1 Setup Script Design

```bash
# voice/setup_voice.sh

#!/bin/bash
# Voice capabilities setup script
# Downloads and caches voice models (~700MB total)

set -e  # Exit on error

echo "🎙️ Sentinel Voice Setup"
echo "======================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ required (found $python_version)"
    exit 1
fi
echo "✅ Python $python_version"
echo ""

# Check disk space
echo "Checking disk space..."
available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
required_space=2

if [ "$available_space" -lt "$required_space" ]; then
    echo "❌ Insufficient disk space (need ${required_space}GB, have ${available_space}GB)"
    exit 1
fi
echo "✅ Sufficient disk space"
echo ""

# Create models directory
echo "Creating models directory..."
mkdir -p models
echo "✅ Models directory created"
echo ""

# Download Whisper model
echo "📥 Downloading Whisper STT model (base, ~150MB)..."
echo "This may take a few minutes..."
python3 -c "
from faster_whisper import WhisperModel
import sys

try:
    print('Loading Whisper base model...')
    model = WhisperModel('base', device='cpu', compute_type='int8')
    print('✅ Whisper model cached successfully')
except Exception as e:
    print(f'❌ Failed to download Whisper model: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Whisper setup failed"
    exit 1
fi
echo ""

# Download XTTS model
echo "📥 Downloading XTTS TTS model (~500MB)..."
echo "This may take several minutes..."
python3 -c "
from TTS.api import TTS
import sys

try:
    print('Loading XTTS v2 model...')
    tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to('cpu')
    print('✅ XTTS model cached successfully')
except Exception as e:
    print(f'❌ Failed to download XTTS model: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ XTTS setup failed"
    exit 1
fi
echo ""

# Verify audio devices
echo "🔊 Checking audio devices..."
python3 -c "
import sounddevice as sd
import sys

try:
    devices = sd.query_devices()
    print('Available audio devices:')
    print(devices)
    print('')
    
    # Check for input device
    input_devices = [d for d in sd.query_devices() if d['max_input_channels'] > 0]
    if not input_devices:
        print('⚠️  Warning: No input devices (microphones) found')
        print('   Voice input will not work without a microphone')
    else:
        print(f'✅ Found {len(input_devices)} input device(s)')
    
    # Check for output device
    output_devices = [d for d in sd.query_devices() if d['max_output_channels'] > 0]
    if not output_devices:
        print('⚠️  Warning: No output devices (speakers) found')
        print('   Voice output will not work without speakers')
    else:
        print(f'✅ Found {len(output_devices)} output device(s)')
        
except Exception as e:
    print(f'⚠️  Could not check audio devices: {e}')
    print('   Voice features may not work properly')
"
echo ""

# Summary
echo "✅ Voice setup complete!"
echo ""
echo "Models cached in: ~/.cache/huggingface/"
echo "Estimated disk usage: ~700MB"
echo ""
echo "Next steps:"
echo "1. Ensure your .env file has GOOGLE_API_KEY set"
echo "2. Run: streamlit run app.py"
echo "3. Click 'Start Call' to test voice features"
echo ""
echo "Troubleshooting:"
echo "- If microphone doesn't work, check system permissions"
echo "- If models fail to load, check internet connection"
echo "- For audio issues, run: python3 -c 'import sounddevice as sd; print(sd.query_devices())'"
```

### 10.2 Installation Instructions

**Step 1: Install Dependencies**
```bash
# Install voice dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import pipecat; import faster_whisper; import TTS; print('✅ All packages installed')"
```

**Step 2: Run Setup Script**
```bash
# Make script executable
chmod +x voice/setup_voice.sh

# Run setup (downloads models)
./voice/setup_voice.sh
```

**Step 3: Configure Environment**
```bash
# Add to .env file
echo "VOICE_ENABLED=true" >> .env
echo "VOICE_STT_MODEL=base" >> .env
echo "VOICE_MAX_SENTENCES=2" >> .env
```

**Step 4: Test Installation**
```bash
# Test audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Test model loading
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Start application
streamlit run app.py
```

### 10.3 System Requirements

**Minimum Requirements:**
- Python 3.10+
- 4GB RAM
- 2GB free disk space
- Microphone (for voice input)
- Speakers/headphones (for voice output)
- Internet connection (for initial setup and Gemini API)

**Recommended Requirements:**
- Python 3.11+
- 8GB RAM
- 5GB free disk space
- USB microphone or headset
- Dedicated speakers
- Stable internet connection

**Operating System Support:**
- Linux: Full support
- macOS: Full support
- Windows: Full support (with WSL recommended)



## 11. Security and Privacy Considerations

### 11.1 Audio Data Handling

**Local Processing:**
- All STT/TTS processing happens locally (no audio sent to external services)
- Audio data never leaves the user's machine except for LLM text
- Microphone access requires explicit user permission

**Data Retention:**
- Audio streams are not recorded or stored
- Transcriptions stored only in session memory
- Session data cleared on browser close
- No persistent audio logs

**Permissions:**
```python
# Audio permission handling

async def request_microphone_permission():
    """Request microphone access with clear user consent"""
    try:
        # Browser will prompt for permission
        stream = await navigator.mediaDevices.getUserMedia({'audio': True})
        return True
    except PermissionDeniedError:
        logger.warning("Microphone permission denied by user")
        return False
    except NotFoundError:
        logger.error("No microphone device found")
        return False
```

### 11.2 Input Validation

**Voice Input Sanitization:**
```python
def sanitize_transcription(text: str) -> str:
    """Sanitize STT output before processing"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Limit length
    max_length = 500  # Reasonable for voice input
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Transcription truncated to {max_length} chars")
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    return text
```

**Injection Prevention:**
- Voice transcriptions pass through same validation as text input
- Existing `validate_input()` and `sanitize_input()` functions apply
- No special characters in voice bypass validation

### 11.3 Resource Limits

**Memory Management:**
```python
# Prevent memory exhaustion

class VoicePipelineHandler:
    MAX_MEMORY_MB = 3000  # 3GB limit
    
    async def _check_memory_usage(self):
        """Monitor memory usage"""
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > self.MAX_MEMORY_MB:
            logger.error(f"Memory limit exceeded: {memory_mb}MB")
            await self.stop()
            raise MemoryError("Voice pipeline exceeded memory limit")
```

**Rate Limiting:**
- Voice calls subject to same Gemini API rate limits
- Maximum call duration: 30 minutes (configurable)
- Cooldown period between calls if needed

### 11.4 Error Information Disclosure

**Safe Error Messages:**
```python
# Don't expose internal details to users

class UserFacingError(Exception):
    """Errors safe to show to users"""
    pass

def handle_error(error: Exception) -> str:
    """Convert internal errors to user-safe messages"""
    # Log full error internally
    logger.error(f"Internal error: {error}", exc_info=True)
    
    # Return generic message to user
    if isinstance(error, UserFacingError):
        return str(error)
    else:
        return "An unexpected error occurred. Please try again."
```



## 12. Monitoring and Observability

### 12.1 Logging Strategy

**Log Levels:**
```python
# voice/logging_config.py

import logging

# Configure voice-specific logger
voice_logger = logging.getLogger('sentinel.voice')
voice_logger.setLevel(logging.INFO)

# Log format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
voice_logger.addHandler(console_handler)

# File handler (optional)
file_handler = logging.FileHandler('logs/voice.log')
file_handler.setFormatter(formatter)
voice_logger.addHandler(file_handler)
```

**Key Log Points:**
```python
# In voice_processor.py
logger.info(f"Voice input received: {text[:50]}...")
logger.info(f"Voice output generated: {response[:50]}...")
logger.warning(f"Response truncated from {original_len} to {truncated_len} sentences")

# In pipecat_handler.py
logger.info("Voice pipeline initializing...")
logger.info("Voice pipeline started successfully")
logger.info(f"Voice call duration: {duration}s")
logger.error(f"Pipeline error: {error}", exc_info=True)

# In app.py
logger.info(f"User started voice call - session: {session_id}")
logger.info(f"User ended voice call - duration: {duration}s")
```

### 12.2 Metrics Collection

**Latency Metrics:**
```python
@dataclass
class VoiceMetrics:
    """Metrics for voice pipeline performance"""
    session_id: str
    timestamp: datetime
    
    # Latency metrics (seconds)
    stt_latency: float
    llm_latency: float
    tts_latency: float
    total_latency: float
    
    # Quality metrics
    transcription_length: int
    response_length: int
    sentences_truncated: int
    
    # Error tracking
    errors_count: int
    error_types: List[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging"""
        return {
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'latency': {
                'stt': self.stt_latency,
                'llm': self.llm_latency,
                'tts': self.tts_latency,
                'total': self.total_latency
            },
            'quality': {
                'transcription_length': self.transcription_length,
                'response_length': self.response_length,
                'sentences_truncated': self.sentences_truncated
            },
            'errors': {
                'count': self.errors_count,
                'types': self.error_types
            }
        }
```

**Metrics Logging:**
```python
# Log metrics after each voice turn
metrics = VoiceMetrics(
    session_id=session_id,
    timestamp=datetime.now(),
    stt_latency=stt_time,
    llm_latency=llm_time,
    tts_latency=tts_time,
    total_latency=total_time,
    transcription_length=len(transcription),
    response_length=len(response),
    sentences_truncated=truncated_count,
    errors_count=0,
    error_types=[]
)

logger.info(f"Voice metrics: {json.dumps(metrics.to_dict())}")
```

### 12.3 Health Checks

**Pipeline Health:**
```python
class VoicePipelineHandler:
    
    def get_health_status(self) -> dict:
        """Get current health status"""
        return {
            'status': 'healthy' if self.is_running else 'stopped',
            'pipeline_initialized': self.pipeline is not None,
            'uptime_seconds': self._get_uptime(),
            'memory_usage_mb': self._get_memory_usage(),
            'last_error': self._last_error,
            'error_count': self._error_count,
            'models_loaded': {
                'whisper': self._whisper_loaded,
                'xtts': self._xtts_loaded
            }
        }
```

**Streamlit Health Display:**
```python
# In app.py - optional debug panel

with st.expander("🔧 Voice System Status"):
    if st.session_state.voice_handler:
        health = st.session_state.voice_handler.get_health_status()
        st.json(health)
    else:
        st.info("Voice system not initialized")
```



## 13. Future Enhancements (Out of Scope)

### 13.1 Potential Improvements

**Phase 2 Features:**
- Real-time interruption handling (barge-in)
- Multi-language support (Spanish, French, etc.)
- Voice activity detection tuning
- Custom wake word ("Hey Sentinel")
- Voice authentication/speaker identification

**Phase 3 Features:**
- WebRTC for browser-based voice
- Mobile app support
- Voice analytics dashboard
- A/B testing different voices
- Emotion detection in voice

**Performance Optimizations:**
- GPU acceleration for faster inference
- Smaller quantized models (int4)
- Streaming STT/TTS for lower latency
- Edge deployment for offline operation

### 13.2 Known Limitations

**Current Limitations:**
- English only (XTTS supports multilingual but not implemented)
- No barge-in (user must wait for agent to finish)
- CPU-only (no GPU acceleration)
- No voice customization (pitch, speed, etc.)
- Single user at a time (no concurrent calls)

**Technical Debt:**
- Streamlit async handling is limited (may need refactoring)
- No persistent metrics storage (logs only)
- Limited error recovery strategies
- No automated performance testing

### 13.3 Migration Path

**From Text to Voice:**
1. Deploy voice as optional feature (VOICE_ENABLED=false by default)
2. Gather user feedback and metrics
3. Optimize based on real-world usage
4. Gradually increase adoption
5. Eventually make voice the primary interface

**Backward Compatibility:**
- Text interface remains fully functional
- Voice can be disabled via config
- No breaking changes to existing APIs
- Conversation state shared between interfaces



## 14. Implementation Checklist

### 14.1 Task 1: Dependencies & Setup
- [ ] Update requirements.txt with voice dependencies
- [ ] Create voice/setup_voice.sh script
- [ ] Add voice configuration to src/core/config.py
- [ ] Test model downloads on clean environment
- [ ] Verify audio device detection
- [ ] Document setup process in README

### 14.2 Task 2: Voice Processor
- [ ] Create voice/voice_processor.py
- [ ] Implement SentinelVoiceProcessor class
- [ ] Implement sentence limiting logic
- [ ] Integrate with process_message()
- [ ] Add logging and metrics
- [ ] Write unit tests
- [ ] Test with mock frames

### 14.3 Task 3: Pipecat Pipeline
- [ ] Create voice/pipecat_handler.py
- [ ] Implement VoicePipelineHandler class
- [ ] Configure Whisper STT service
- [ ] Configure XTTS TTS service
- [ ] Build complete pipeline
- [ ] Implement lifecycle management (start/stop)
- [ ] Add error handling
- [ ] Test end-to-end flow
- [ ] Measure and optimize latency

### 14.4 Task 4: Streamlit Interface
- [ ] Add voice session state initialization
- [ ] Create voice UI layout (two columns)
- [ ] Implement Start Call button
- [ ] Implement End Call button
- [ ] Add status indicators
- [ ] Display transcriptions
- [ ] Display responses
- [ ] Handle async pipeline operations
- [ ] Test state synchronization
- [ ] Test error scenarios
- [ ] User acceptance testing

### 14.5 Documentation & Deployment
- [ ] Update README with voice features
- [ ] Add troubleshooting guide
- [ ] Document system requirements
- [ ] Create user guide for voice features
- [ ] Add example .env configuration
- [ ] Test on different operating systems
- [ ] Performance benchmarking
- [ ] Security review

## 15. Success Criteria

### 15.1 Functional Requirements
✅ User can start voice call with single button click  
✅ Speech is transcribed accurately (>90% accuracy for clear speech)  
✅ Agent responses are limited to 2 sentences  
✅ Voice output is clear and natural-sounding  
✅ User can end call cleanly  
✅ Conversation state is maintained across text/voice  
✅ All existing conversation flows work via voice

### 15.2 Performance Requirements
✅ Total latency < 2 seconds (95th percentile)  
✅ STT latency < 1 second  
✅ LLM latency < 1 second  
✅ TTS latency < 1 second  
✅ Pipeline initialization < 3 seconds  
✅ Memory usage < 3GB during active call

### 15.3 Quality Requirements
✅ No breaking changes to existing text interface  
✅ Graceful error handling with user-friendly messages  
✅ Clean resource cleanup on call termination  
✅ Comprehensive logging for debugging  
✅ Unit test coverage > 80%  
✅ Integration tests pass  
✅ Manual testing checklist completed

## 16. Appendix

### 16.1 Dependencies Reference

**Core Framework:**
- pipecat-ai[local]>=0.0.30 - Voice pipeline orchestration

**STT/TTS Engines:**
- faster-whisper>=0.10.0 - Speech-to-text
- TTS>=0.22.0 - Text-to-speech (XTTS)

**Audio I/O:**
- pyaudio>=0.2.14 - Audio device interface
- sounddevice>=0.4.6 - Audio streaming
- numpy>=1.24.0 - Audio data processing

**Existing:**
- streamlit>=1.28.0 - UI framework
- google-genai>=0.1.0 - LLM integration
- pydantic>=2.12.5 - Configuration management

### 16.2 Configuration Reference

**Environment Variables:**
```bash
# Required (existing)
GOOGLE_API_KEY=your_api_key_here

# Voice STT
VOICE_STT_MODEL=base
VOICE_STT_DEVICE=cpu
VOICE_STT_COMPUTE_TYPE=int8

# Voice TTS
VOICE_TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
VOICE_TTS_LANGUAGE=en
VOICE_TTS_SPEED=1.0

# Voice Pipeline
VOICE_SILENCE_THRESHOLD=0.5
VOICE_SILENCE_DURATION=0.8
VOICE_MAX_SENTENCES=2
VOICE_ENABLED=true
```

### 16.3 File Structure

```
sentinel-insurance-agent/
├── app.py                              # Extended with voice UI
├── requirements.txt                    # Updated with voice deps
├── .env                               # Voice config added
├── README.md                          # Updated with voice docs
├── src/
│   ├── core/
│   │   ├── config.py                  # Extended with voice settings
│   │   ├── conversation_flow_manager.py  # No changes
│   │   ├── models.py                  # No changes
│   │   └── prompts.py                 # No changes
│   └── integration/
│       └── gemini_client.py           # No changes
├── voice/                             # NEW
│   ├── __init__.py
│   ├── setup_voice.sh                 # Model download script
│   ├── voice_processor.py             # Pipecat processor
│   └── pipecat_handler.py             # Pipeline orchestration
├── tests/                             # NEW
│   ├── test_voice_processor.py
│   ├── test_pipecat_handler.py
│   └── integration/
│       └── test_voice_e2e.py
└── logs/                              # NEW
    └── voice.log
```

---

**Design Document Version:** 1.0  
**Last Updated:** 2026-02-01  
**Status:** Ready for Implementation
