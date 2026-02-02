# Design Document: Voice-First Sentinel Command Center

## Overview

This design transforms the Sentinel Insurance Agent from a hybrid text-and-voice system into a pure voice-first command center experience. The refactoring focuses on three main areas:

1. **Enhanced Tool Logic**: Extending the `lookup_policy` tool to return structured escalation indicators
2. **Automatic Escalation Flow**: Updating the conversation flow manager to detect and handle escalation automatically
3. **Command Center UI**: Redesigning the interface with real-time metrics, live transcription, and a dark theme aesthetic

The design maintains the existing voice processing pipeline (Faster-Whisper STT, Piper TTS, Gemini 2.5 Flash Lite) while adding performance monitoring and improving the user experience for voice-only interactions.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Center UI                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Stats Dashboard (Latency, Tokens, Model)            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Live Transcription Container (st.empty())           │  │
│  │  - User Speech (transcribed)                         │  │
│  │  - Agent Responses                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Audio Recorder (audio_recorder_streamlit)           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Voice Processing Pipeline                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Faster-  │───▶│  Gemini  │───▶│  Piper   │             │
│  │ Whisper  │    │  2.5 FL  │    │   TTS    │             │
│  │  (STT)   │    │  (LLM)   │    │          │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│       │               │                │                    │
│       └───────────────┴────────────────┘                    │
│              Latency Tracking                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         Conversation Flow Manager                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Intent Detection → State Transition                 │  │
│  │  Tool Result Analysis → Escalation Detection         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Enhanced Tools                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ lookup_policy│  │  triage_and  │  │ get_available│     │
│  │ (escalation) │  │  _escalate   │  │    _slots    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Component Interactions

1. **User speaks** → Audio Recorder captures audio bytes
2. **STT Processing** → Faster-Whisper transcribes to text (latency tracked)
3. **Conversation Flow** → Processes message, detects intent, transitions state
4. **LLM Processing** → Gemini generates response with tool calling (latency tracked)
5. **Escalation Detection** → Flow manager checks tool results for escalation indicators
6. **TTS Processing** → Piper synthesizes speech (latency tracked)
7. **UI Update** → Dashboard shows metrics, Live Transcription shows conversation
8. **Audio Playback** → User hears response with autoplay

## Components and Interfaces

### 1. Enhanced Tool Response Structure

All tools will return a standardized response structure:

```python
{
    "status": str,  # "success", "not_supported", "error"
    "action": str,  # "continue", "escalate", "retry"
    "escalation_required": bool,
    "data": Any,  # Tool-specific response data
    "message": str  # Human-readable message
}
```

### 2. Updated lookup_policy Tool

**File**: `src/core/tools.py`

**Current Implementation**:
```python
def lookup_policy(policy_number: str) -> str:
    mock_db = {
        "POL123": "Status: Active. Type: Auto. Coverage: Full Comprehensive. Holder: John.",
        "FIRE99": "Status: Active. Type: Fire/Home. Coverage: Structure & Contents. Holder: Jane.",
    }
    return mock_db.get(policy_number.upper(), "Error: Policy number not found.")
```

**New Implementation**:
```python
def lookup_policy(policy_number: str, operation: str = "lookup") -> Dict[str, Any]:
    """
    Retrieves policy details or indicates if escalation is needed.
    
    Args:
        policy_number: The policy number to look up
        operation: The operation type (lookup, change_address, claim_status, update_beneficiary)
    
    Returns:
        Structured response with escalation indicator
    """
    # Unsupported operations that require human intervention
    unsupported_operations = [
        "change_address", "update_address", "address_change",
        "claim_status", "check_claim", "claim_inquiry",
        "update_beneficiary", "change_beneficiary", "beneficiary_update"
    ]
    
    if operation.lower() in unsupported_operations:
        return {
            "status": "not_supported",
            "action": "escalate",
            "escalation_required": True,
            "data": None,
            "message": f"Operation '{operation}' requires specialist assistance"
        }
    
    # Standard policy lookup
    mock_db = {
        "POL123": {
            "status": "Active",
            "type": "Auto",
            "coverage": "Full Comprehensive",
            "holder": "John"
        },
        "FIRE99": {
            "status": "Active",
            "type": "Fire/Home",
            "coverage": "Structure & Contents",
            "holder": "Jane"
        }
    }
    
    policy_data = mock_db.get(policy_number.upper())
    
    if policy_data:
        return {
            "status": "success",
            "action": "continue",
            "escalation_required": False,
            "data": policy_data,
            "message": f"Policy {policy_number}: {policy_data}"
        }
    else:
        return {
            "status": "error",
            "action": "retry",
            "escalation_required": False,
            "data": None,
            "message": "Policy number not found"
        }
```

### 3. Conversation Flow Manager Updates

**File**: `src/core/conversation_flow_manager.py`

**New Function**: `detect_escalation_from_tool_result`

```python
def detect_escalation_from_tool_result(tool_result: Any) -> bool:
    """
    Detect if a tool result indicates escalation is needed.
    
    Args:
        tool_result: The result returned from a tool call
    
    Returns:
        True if escalation is required, False otherwise
    """
    # Handle dictionary responses
    if isinstance(tool_result, dict):
        if tool_result.get("escalation_required", False):
            return True
        if tool_result.get("status") == "not_supported":
            return True
        if tool_result.get("action") == "escalate":
            return True
    
    # Handle string responses (legacy format)
    if isinstance(tool_result, str):
        escalation_keywords = ["not_supported", "escalate", "specialist", "human agent"]
        return any(keyword in tool_result.lower() for keyword in escalation_keywords)
    
    return False
```

**Updated**: `process_message` function

The function will be enhanced to:
1. Check tool results for escalation indicators after LLM response
2. If escalation detected, append escalation message
3. Automatically trigger `triage_and_escalate` tool with collected user info

```python
def process_message(message: str, state: ConversationStateData) -> Dict[str, Any]:
    """Enhanced message processing with escalation detection"""
    
    # ... existing intent detection and info extraction ...
    
    # Generate response (may include tool calls)
    response = generate_response(full_prompt, context, state.conversation_history)
    
    # NEW: Check if escalation is needed
    # This would require access to tool call results from Gemini
    # We'll need to modify the gemini_client to return tool results
    
    escalation_needed = False
    # Check conversation context for escalation indicators
    if "not_supported" in response.lower() or "specialist" in response.lower():
        escalation_needed = True
    
    if escalation_needed:
        # Append escalation message
        escalation_msg = "I'll need a specialist for that. Let me get someone from the department on the line."
        response = f"{response}\n\n{escalation_msg}"
        
        # Trigger escalation tool if we have required info
        if state.user_info.name and state.user_info.contact_info:
            issue_desc = message  # Use the user's original message as issue description
            triage_result = triage_and_escalate(
                name=state.user_info.name,
                issue_description=issue_desc,
                phone=state.user_info.contact_info
            )
            response = f"{response}\n\n{triage_result}"
    
    # ... rest of existing logic ...
```

### 4. Latency Tracking System

**New File**: `src/core/metrics.py`

```python
from dataclasses import dataclass, field
from typing import List
import time
from contextlib import contextmanager

@dataclass
class LatencyMetrics:
    """Track latency for different processing stages"""
    stt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    token_count: int = 0
    model_name: str = ""
    
    def to_dict(self) -> dict:
        return {
            "stt_ms": round(self.stt_latency_ms, 2),
            "llm_ms": round(self.llm_latency_ms, 2),
            "tts_ms": round(self.tts_latency_ms, 2),
            "total_ms": round(self.total_latency_ms, 2),
            "tokens": self.token_count,
            "model": self.model_name
        }

@contextmanager
def track_latency(metric_name: str):
    """Context manager for tracking operation latency"""
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        # Return elapsed time for caller to store
        return elapsed
```

**Integration Points**:
- `StreamlitVoiceHandler.transcribe_audio()` - Track STT latency
- `gemini_client.generate_response()` - Track LLM latency
- `StreamlitVoiceHandler.synthesize_speech()` - Track TTS latency

### 5. Command Center UI Components

**File**: `app.py` (complete rewrite)

**Main Structure**:
```python
def main():
    st.set_page_config(
        page_title="Sentinel Command Center",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply dark theme
    apply_command_center_theme()
    
    # Initialize session state
    initialize_session_state()
    
    # Render command center interface
    render_command_center()

def apply_command_center_theme():
    """Apply dark theme CSS"""
    st.markdown("""
    <style>
    /* Dark theme with high contrast */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Metrics dashboard styling */
    .metric-card {
        background-color: #1e2130;
        border: 1px solid #2e3440;
        border-radius: 8px;
        padding: 16px;
        color: #eceff4;
    }
    
    /* Live transcription styling */
    .transcription-container {
        background-color: #1e2130;
        border: 2px solid #4c566a;
        border-radius: 12px;
        padding: 24px;
        min-height: 400px;
        font-family: 'Courier New', monospace;
    }
    
    .user-speech {
        color: #88c0d0;
        font-weight: bold;
    }
    
    .agent-response {
        color: #a3be8c;
        font-weight: bold;
    }
    
    /* Status indicators */
    .status-active {
        color: #a3be8c;
    }
    
    .status-processing {
        color: #ebcb8b;
    }
    
    .status-error {
        color: #bf616a;
    }
    </style>
    """, unsafe_allow_html=True)

def render_command_center():
    """Main command center interface"""
    
    # Header
    st.markdown("# 🛡️ SENTINEL COMMAND CENTER")
    st.markdown("---")
    
    # Stats Dashboard
    render_stats_dashboard()
    
    st.markdown("---")
    
    # Live Transcription
    render_live_transcription()
    
    st.markdown("---")
    
    # Voice Input Section
    render_voice_input()

def render_stats_dashboard():
    """Render metrics dashboard at top"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    metrics = st.session_state.get("current_metrics", {})
    
    with col1:
        st.metric("STT Latency", f"{metrics.get('stt_ms', 0)} ms")
    
    with col2:
        st.metric("LLM Latency", f"{metrics.get('llm_ms', 0)} ms")
    
    with col3:
        st.metric("TTS Latency", f"{metrics.get('tts_ms', 0)} ms")
    
    with col4:
        st.metric("Tokens", metrics.get('tokens', 0))
    
    with col5:
        st.metric("Model", metrics.get('model', 'N/A'))

def render_live_transcription():
    """Render live transcription container"""
    st.markdown("### 📡 LIVE TRANSCRIPTION")
    
    # Use st.empty() for real-time updates
    transcription_container = st.empty()
    
    # Build transcription display
    messages = st.session_state.get("messages", [])
    transcription_html = '<div class="transcription-container">'
    
    for msg in messages:
        role_class = "user-speech" if msg["role"] == "user" else "agent-response"
        role_label = "USER" if msg["role"] == "user" else "SENTINEL"
        transcription_html += f'<p><span class="{role_class}">[{role_label}]</span> {msg["content"]}</p>'
    
    transcription_html += '</div>'
    
    transcription_container.markdown(transcription_html, unsafe_allow_html=True)

def render_voice_input():
    """Render voice input section"""
    st.markdown("### 🎤 VOICE INPUT")
    
    # Model loading
    if not st.session_state.models_loaded:
        if st.button("🚀 INITIALIZE VOICE SYSTEMS", type="primary"):
            with st.spinner("Loading voice models..."):
                load_voice_models()
                # Generate and play welcome message
                play_welcome_message()
        return
    
    # Audio recorder
    audio_bytes = audio_recorder(
        text="",
        recording_color="#bf616a",
        neutral_color="#5e81ac",
        icon_name="microphone",
        icon_size="3x",
        key="voice_recorder"
    )
    
    if audio_bytes:
        process_voice_input(audio_bytes)
```

### 6. Welcome Message System

**New Function in app.py**:

```python
def play_welcome_message():
    """Generate and play welcome message after model loading"""
    try:
        welcome_text = "Hello! I'm Sentinel. How can I help you today?"
        
        # Add to messages
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_text,
            "source": "voice"
        })
        
        # Generate TTS
        handler = st.session_state.voice_handler
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            welcome_audio_path = tmp.name
        
        handler.synthesize_speech(welcome_text, welcome_audio_path)
        
        # Store in session state for playback
        with open(welcome_audio_path, "rb") as f:
            st.session_state.last_response_audio = f.read()
        
        os.unlink(welcome_audio_path)
        
        st.success("✅ Voice systems ready!")
        st.rerun()
        
    except Exception as e:
        logger.error(f"Welcome message error: {e}")
        st.error("Failed to generate welcome message")
```

## Data Models

### Enhanced ConversationStateData

No changes needed to the existing `ConversationStateData` model. It already supports:
- `current_state`: Conversation state tracking
- `user_info`: User information collection
- `conversation_history`: Message history
- `context`: Additional context storage

### New LatencyMetrics Model

```python
@dataclass
class LatencyMetrics:
    stt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    token_count: int = 0
    model_name: str = ""
```

### Enhanced Tool Response Model

```python
@dataclass
class ToolResponse:
    status: str  # "success", "not_supported", "error"
    action: str  # "continue", "escalate", "retry"
    escalation_required: bool
    data: Any
    message: str
```

## Correctness Properties

