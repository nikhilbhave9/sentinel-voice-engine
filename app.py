import streamlit as st
import streamlit.components.v1 as components
import logging
import re
import tempfile
import os
import hashlib

from audio_recorder_streamlit import audio_recorder

from src.core.models import ConversationStateData
from src.core.conversation_flow_manager import process_message
from src.core.config import get_settings
from src.voice.streamlit_voice_handler import StreamlitVoiceHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_command_center_theme():
    """Apply dark theme CSS for command center aesthetic"""
    st.markdown("""
    <style>
    /* Hide Streamlit header and menu */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Hide the main menu button (hamburger) */
    button[kind="header"] {
        display: none !important;
    }
    
    /* Hide deploy button */
    .stDeployButton {
        display: none !important;
    }
    
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
    
    /* Style Streamlit metric containers */
    [data-testid="stMetricValue"] {
        color: #88c0d0;
        font-size: 1.5rem;
        font-weight: bold;
    }
    
    [data-testid="stMetricLabel"] {
        color: #d8dee9;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Live transcription styling */
    .transcription-container {
        background-color: #1e2130;
        border: 2px solid #4c566a;
        border-radius: 12px;
        padding: 24px;
        min-height: 400px;
        font-family: 'Courier New', monospace;
        color: #eceff4;
        line-height: 1.6;
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
    
    /* Chat message styling for dark theme */
    .stChatMessage {
        background-color: #1e2130;
        border: 1px solid #2e3440;
    }
    
    /* Enhanced Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #5e81ac 0%, #81a1c1 100%);
        color: #eceff4;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 12px 24px;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #81a1c1 0%, #88c0d0 100%);
        box-shadow: 0 6px 12px rgba(136, 192, 208, 0.4);
        transform: translateY(-2px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Audio recorder styling */
    .stAudio {
        background-color: #1e2130;
        border-radius: 8px;
        padding: 8px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #1e2130;
        color: #eceff4;
        border-radius: 6px;
    }
    
    /* Markdown text color */
    .stMarkdown {
        color: #eceff4;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #88c0d0 !important;
    }
    
    /* Divider */
    hr {
        border-color: #4c566a;
        opacity: 0.5;
    }
    
    /* Caption text */
    .stCaption {
        color: #d8dee9;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #88c0d0 !important;
    }
    
    /* Info box styling */
    .stAlert {
        background-color: #1e2130;
        border-left: 4px solid #5e81ac;
        color: #eceff4;
    }
    
    /* Success box styling */
    [data-testid="stSuccess"] {
        background-color: #1e2130;
        border-left: 4px solid #a3be8c;
        color: #eceff4;
    }
    
    /* Error box styling */
    [data-testid="stError"] {
        background-color: #1e2130;
        border-left: 4px solid #bf616a;
        color: #eceff4;
    }
    
    /* Pulse animation for active status */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Glowing Orb Styles */
    .orb-container {
        position: relative;
        width: 200px;
        height: 200px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .orb {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        background: linear-gradient(135deg, #5e81ac 0%, #88c0d0 50%, #81a1c1 100%);
        box-shadow: 0 0 40px rgba(136, 192, 208, 0.6),
                    0 0 80px rgba(136, 192, 208, 0.4),
                    inset 0 0 40px rgba(255, 255, 255, 0.2);
        animation: orbPulse 3s ease-in-out infinite;
        position: relative;
        z-index: 2;
    }
    
    .orb-glow {
        position: absolute;
        width: 200px;
        height: 200px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(136, 192, 208, 0.4) 0%, transparent 70%);
        animation: glowPulse 3s ease-in-out infinite;
        z-index: 1;
    }
    
    @keyframes orbPulse {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 40px rgba(136, 192, 208, 0.6),
                        0 0 80px rgba(136, 192, 208, 0.4),
                        inset 0 0 40px rgba(255, 255, 255, 0.2);
        }
        50% {
            transform: scale(1.05);
            box-shadow: 0 0 60px rgba(136, 192, 208, 0.8),
                        0 0 120px rgba(136, 192, 208, 0.6),
                        inset 0 0 60px rgba(255, 255, 255, 0.3);
        }
    }
    
    @keyframes glowPulse {
        0%, 100% {
            transform: scale(1);
            opacity: 0.6;
        }
        50% {
            transform: scale(1.1);
            opacity: 0.8;
        }
    }
    
    /* Hide the recording expander */
    .streamlit-expanderHeader {
        display: none !important;
    }
    
    div[data-testid="stExpander"] {
        display: none !important;
    }
    
    /* Hide default audio controls */
    audio {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_stats_dashboard():
    """Render metrics dashboard at top of interface"""
    st.markdown("### 📊 PERFORMANCE METRICS")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Get metrics from session state, default to zeros if not available
    metrics = st.session_state.get("current_metrics", {})
    
    with col1:
        stt_latency = metrics.get('stt_ms', 0)
        st.metric("STT Latency", f"{stt_latency} ms")
    
    with col2:
        llm_latency = metrics.get('llm_ms', 0)
        st.metric("LLM Latency", f"{llm_latency} ms")
    
    with col3:
        tts_latency = metrics.get('tts_ms', 0)
        st.metric("TTS Latency", f"{tts_latency} ms")
    
    with col4:
        token_count = metrics.get('tokens', 0)
        st.metric("Token Count", token_count)
    
    with col5:
        model_name = metrics.get('model', 'N/A')
        st.metric("Model", model_name)


def render_live_transcription():
    """Render live transcription container with real-time updates
    
    Displays conversation history in a command center style with:
    - User speech in cyan with [USER] label
    - Agent responses in green with [SENTINEL] label
    - Chronological order
    - Real-time updates using st.empty()
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    st.markdown("### 📡 LIVE TRANSCRIPTION")
    
    # Use st.empty() for real-time updates
    transcription_container = st.empty()
    
    # Get messages from session state
    messages = st.session_state.get("messages", [])
    
    # Build HTML display with visual formatting
    transcription_html = '<div class="transcription-container">'
    
    if not messages:
        transcription_html += '<p style="color: #d8dee9; font-style: italic;">Waiting for conversation to begin...</p>'
    else:
        # Display messages in chronological order
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Distinguish user vs agent with different colors and labels
            if role == "user":
                role_class = "user-speech"
                role_label = "USER"
            else:
                role_class = "agent-response"
                role_label = "SENTINEL"
            
            # Build message HTML with role label and content
            transcription_html += f'<p><span class="{role_class}">[{role_label}]</span> {content}</p>'
    
    transcription_html += '</div>'
    
    # Update the container with the built HTML
    transcription_container.markdown(transcription_html, unsafe_allow_html=True)


def main():
    """Application entry point - Single-page voice-first command center layout
    
    Layout structure:
    1. Header
    2. Side-by-side layout:
       - Left: Voice Interface (with clickable orb)
       - Right: Live Transcription
    3. Stats Dashboard - Performance metrics (bottom)
    
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    config_settings = get_settings()
    
    st.set_page_config(
        page_title="Sentinel Insurance Agent",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply dark theme
    apply_command_center_theme()
    
    # Header
    st.markdown(
        "<h1 style='text-align: center;'>🛡️ SENTINEL Insurance Agent</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; font-style: italic;'>First-line agentic AI insurance query resolver</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    
    initialize_session_state()
    
    # Side-by-side layout: Voice Interface (left) and Transcription (right)
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        render_voice_interface()
    
    with col2:
        render_live_transcription()
    
    # Stats Dashboard at bottom
    st.markdown("---")
    render_stats_dashboard()


def initialize_session_state():
    """Initialize session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Welcome message will be generated automatically after model loading
    
    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = ConversationStateData()
    
    if "voice_handler" not in st.session_state:
        st.session_state.voice_handler = None
        st.session_state.models_loaded = False
    
    # CRITICAL: Track processed audio to prevent re-processing
    if "last_processed_audio_hash" not in st.session_state:
        st.session_state.last_processed_audio_hash = None
    
    # Initialize metrics dashboard with default values
    if "current_metrics" not in st.session_state:
        st.session_state.current_metrics = {
            "stt_ms": 0,
            "llm_ms": 0,
            "tts_ms": 0,
            "tokens": 0,
            "model": "N/A"
        }
    
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True
        logger.info("Session initialized")


def handle_user_input(user_input: str, is_voice: bool = False):
    """Process user input (text or voice)"""
    try:
        if not validate_input(user_input):
            return
        
        sanitized = sanitize_input(user_input)
        if not sanitized:
            st.warning("Unable to process message.")
            return
        
        # Add to conversation
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "source": "voice" if is_voice else "text"
        })
        
        # Process
        result = process_message(sanitized, st.session_state.conversation_state, source="voice" if is_voice else "text")
        
        # Update state
        st.session_state.conversation_state.current_state = result.get(
            "new_state", 
            st.session_state.conversation_state.current_state
        )
        
        # Store LLM latency metrics in session state
        if "current_metrics" not in st.session_state:
            st.session_state.current_metrics = {}
        st.session_state.current_metrics["llm_ms"] = round(result.get("llm_latency_ms", 0.0), 2)
        st.session_state.current_metrics["tokens"] = result.get("token_count", 0)
        st.session_state.current_metrics["model"] = result.get("model_name", "")
        
        # Get response
        response = result.get("response", "I'm sorry, I couldn't process that.")
        
        # Add response
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "source": "voice" if is_voice else "text"
        })
        
        logger.info(f"Processed {'voice' if is_voice else 'text'} input")
        
    except Exception as e:
        logger.error(f"Error processing input: {e}", exc_info=True)
        st.error("Sorry, technical difficulties.")


def play_welcome_message():
    """Generate and play welcome message after model loading
    
    Generates the welcome message "Hello! I'm Sentinel. How can I help you today?",
    synthesizes it using TTS, stores the audio in session state for autoplay,
    and adds the message to conversation history.
    
    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
    """
    try:
        welcome_text = "Hello! I'm Sentinel. How can I help you today?"
        
        # Add welcome message to conversation history
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_text,
            "source": "voice"
        })
        
        # Generate TTS audio for welcome message
        handler = st.session_state.voice_handler
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            welcome_audio_path = tmp.name
        
        # Synthesize speech with latency tracking
        welcome_audio_path, tts_latency_ms = handler.synthesize_speech(welcome_text, welcome_audio_path)
        
        # Store TTS latency in session state
        if "current_metrics" not in st.session_state:
            st.session_state.current_metrics = {}
        st.session_state.current_metrics["tts_ms"] = round(tts_latency_ms, 2)
        
        # Validate audio was generated
        if os.path.getsize(welcome_audio_path) == 0:
            os.unlink(welcome_audio_path)
            logger.error("Welcome message TTS produced empty audio")
            st.error("Failed to generate welcome message audio")
            return
        
        # Store welcome audio in session state for autoplay
        with open(welcome_audio_path, "rb") as f:
            st.session_state.last_response_audio = f.read()
        
        # Clean up temporary file
        os.unlink(welcome_audio_path)
        
        logger.info("Welcome message generated and ready for playback")
        st.success("✅ Voice systems ready!")
        
    except Exception as e:
        logger.error(f"Welcome message error: {e}", exc_info=True)
        st.error("Failed to generate welcome message")


def render_voice_interface():
    """Render voice interface with clickable glowing orb
    
    The orb acts as the record button with the audio recorder overlaid on top.
    """
    # ---- INIT AUDIO STATE ----
    if "last_response_audio" not in st.session_state:
        st.session_state.last_response_audio = None
    
    if "is_recording" not in st.session_state:
        st.session_state.is_recording = False

    # ---- LOAD MODELS ----
    if not st.session_state.models_loaded:
        # Enhanced initialization UI
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: linear-gradient(135deg, #1a1f35 0%, #2d3250 100%); 
                    border-radius: 20px; border: 2px solid #4c566a; margin: 20px 0; min-height: 600px;
                    display: flex; flex-direction: column; justify-content: center; align-items: center;">
            <div style="font-size: 5rem; margin-bottom: 30px; filter: drop-shadow(0 0 20px rgba(136, 192, 208, 0.5));">🛡️</div>
            <h2 style="color: #88c0d0; margin-bottom: 15px; font-weight: 600; font-size: 2rem;">VOICE SYSTEMS OFFLINE</h2>
            <p style="color: #d8dee9; font-size: 1.2rem; margin-bottom: 40px; opacity: 0.9;">Initialize speech/text models to begin (load time: 5-7 seconds)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Center the button
        if st.button("INITIALIZE VOICE SYSTEMS", type="primary", use_container_width=True):
            with st.spinner("⚡ Loading voice models (~15 seconds)..."):
                try:
                    st.session_state.voice_handler = StreamlitVoiceHandler(
                        st.session_state.conversation_state
                    )
                    _ = st.session_state.voice_handler.stt_model
                    _ = st.session_state.voice_handler.tts_model
                    st.session_state.models_loaded = True
                    
                    # Generate and play welcome message after models load
                    play_welcome_message()
                    st.rerun()
                except Exception as e:
                    logger.error(f"Model loading error: {e}", exc_info=True)
                    st.error(f"Failed to load: {e}")
        return

    # ---- BEAUTIFUL VOICE INTERFACE WITH CLICKABLE ORB ----
    # Use components.html for proper JavaScript execution
    components.html("""
    <div id="voice-interface-container" style="background: linear-gradient(135deg, #1a1f35 0%, #2d3250 100%); 
                border-radius: 20px; border: 2px solid #4c566a; padding: 20px; 
                margin: 10px 0; text-align: center;
                display: flex; flex-direction: column; justify-content: center; align-items: center;
                position: relative;">
        
        <div style="margin: 10px 0;">
            <h3 style="color: #88c0d0; font-size: 1.5rem; margin-bottom: 5px; font-weight: 500;">
                I'm listening...
            </h3>
            <p style="color: #d8dee9; font-size: 1rem; opacity: 0.8; margin-bottom: 15px;">
                Click the orb to toggle recording
            </p>
        </div>
        
        <div id="voice-orb" style="position: relative; margin: 20px auto; width: 220px; height: 220px;">
            <div id="orb-visual" style="width: 200px; height: 200px; margin: 10px auto;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #5e81ac 0%, #88c0d0 50%, #81a1c1 100%);
                        box-shadow: 0 0 60px rgba(136, 192, 208, 0.8),
                                    0 0 120px rgba(136, 192, 208, 0.5),
                                    inset 0 0 60px rgba(255, 255, 255, 0.3);
                        animation: orbPulse 3s ease-in-out infinite;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 4rem;
                        user-select: none;
                        pointer-events: auto;">
                🎤
            </div>
        </div>
        
        <div style="margin: 10px 0;">
            <p style="color: #d8dee9; font-size: 0.9rem; opacity: 0.7;">
                Click to start/stop recording
            </p>
        </div>
    </div>
    
    <style>
    @keyframes orbPulse {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 60px rgba(136, 192, 208, 0.8),
                        0 0 120px rgba(136, 192, 208, 0.5),
                        inset 0 0 60px rgba(255, 255, 255, 0.3);
        }
        50% {
            transform: scale(1.05);
            box-shadow: 0 0 80px rgba(136, 192, 208, 1),
                        0 0 160px rgba(136, 192, 208, 0.7),
                        inset 0 0 80px rgba(255, 255, 255, 0.4);
        }
    }
    </style>
    
    <script>
    // Helper function to get recorder iframe
    function getRecorderIframe() {
        return window.parent.document.querySelector(
            'iframe[title="audio_recorder_streamlit.audio_recorder"]'
        );
    }
    
    // Click handler for toggle behavior
    document.getElementById('orb-visual').addEventListener('click', function() {
        const iframe = getRecorderIframe();
        if (!iframe) return;
        
        // Click the button inside the iframe to toggle recording
        const btn = iframe.contentWindow.document.querySelector("button");
        if (btn) btn.click();
    });
    
    // Position the recorder over the orb
    function positionRecorder() {
        const orb = document.getElementById('orb-visual');
        const iframe = getRecorderIframe();
        if (!orb || !iframe) return;
        
        const rect = orb.getBoundingClientRect();
        const parentRect = window.frameElement.getBoundingClientRect();
        
        iframe.style.left = (parentRect.left + rect.left) + 'px';
        iframe.style.top = (parentRect.top + rect.top) + 'px';
        iframe.style.width = rect.width + 'px';
        iframe.style.height = rect.height + 'px';
    }
    
    // Run positioning after delays to ensure elements are rendered
    setTimeout(positionRecorder, 300);
    setTimeout(positionRecorder, 800);
    setTimeout(positionRecorder, 1500);
    
    // Reposition on window resize
    window.addEventListener('resize', positionRecorder);
    </script>
    """, height=450)
    
    # ---- AUDIO RECORDER OVERLAID ON ORB ----
    # CSS-only styling for the recorder (no JS here)
    st.markdown("""
    <style>
    /* Initially hide the recorder */
    iframe[title="audio_recorder_streamlit.audio_recorder"] {
        position: fixed !important;
        opacity: 0 !important;
        z-index: 1001 !important;
        border-radius: 50% !important;
        pointer-events: none !important;
        width: 200px !important;
        height: 200px !important;
    }
    
    /* Show slightly on hover for debugging */
    iframe[title="audio_recorder_streamlit.audio_recorder"]:hover {
        opacity: 0.05 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render the audio recorder
    audio_bytes = audio_recorder(
        text="",
        recording_color="#bf616a",
        neutral_color="#5e81ac",
        icon_name="microphone",
        icon_size="2x",
        key="voice_recorder"
    )

    # ---- HIDDEN AUDIO PLAYER (NO UGLY WHITE CONTROLS) ----
    if st.session_state.last_response_audio:
        # Use HTML5 audio with autoplay and JavaScript to force playback
        import base64
        audio_base64 = base64.b64encode(st.session_state.last_response_audio).decode()
        
        # Method 1: Use components.html with JavaScript to force playback
        components.html(f"""
        <audio id="response-audio" preload="auto">
            <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
        </audio>
        <script>
        (function() {{
            const audio = document.getElementById('response-audio');
            if (audio) {{
                console.log('Audio element found, attempting playback...');
                
                // Load the audio first
                audio.load();
                
                // Try to play immediately
                const playPromise = audio.play();
                
                if (playPromise !== undefined) {{
                    playPromise.then(function() {{
                        console.log('Audio playback started successfully');
                    }}).catch(function(error) {{
                        console.error('Autoplay failed:', error);
                        
                        // If autoplay fails, try again after a short delay
                        setTimeout(function() {{
                            audio.play().then(function() {{
                                console.log('Second play attempt succeeded');
                            }}).catch(function(e) {{
                                console.error('Second play attempt failed:', e);
                            }});
                        }}, 200);
                    }});
                }}
            }} else {{
                console.error('Audio element not found');
            }}
        }})();
        </script>
        """, height=0)
        
        # Method 2: Also try with st.audio as backup (hidden with CSS)
        st.markdown("""
        <style>
        /* Hide the Streamlit audio player */
        audio[controls] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # This will autoplay in most browsers
        st.audio(st.session_state.last_response_audio, format="audio/wav", autoplay=True)

    # ---- PROCESS NEW AUDIO ----
    if audio_bytes:
        audio_hash = hashlib.md5(audio_bytes).hexdigest()

        if audio_hash == st.session_state.last_processed_audio_hash:
            logger.info("Skipping already processed audio")
            return

        st.session_state.last_processed_audio_hash = audio_hash

        # Recording received - no need to display it, just process
        with st.spinner("🎯 Processing voice input..."):
            try:
                # Save mic audio
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    audio_path = tmp.name

                handler = st.session_state.voice_handler

                # STT with latency tracking
                transcription, stt_latency_ms = handler.transcribe_audio(audio_path)
                os.unlink(audio_path)
                
                # Store STT latency in session state
                if "current_metrics" not in st.session_state:
                    st.session_state.current_metrics = {}
                st.session_state.current_metrics["stt_ms"] = round(stt_latency_ms, 2)

                if not transcription:
                    st.warning("Could not transcribe. Try again.")
                    return

                # LLM + flow
                handle_user_input(transcription, is_voice=True)

                # Get last assistant message
                last_response = None
                for msg in reversed(st.session_state.messages):
                    if msg["role"] == "assistant":
                        last_response = msg["content"]
                        break

                if not last_response:
                    return

                # TTS with latency tracking
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    response_path = tmp.name

                response_path, tts_latency_ms = handler.synthesize_speech(last_response, response_path)
                
                # Store TTS latency in session state
                st.session_state.current_metrics["tts_ms"] = round(tts_latency_ms, 2)

                # Validate audio
                if os.path.getsize(response_path) == 0:
                    os.unlink(response_path)
                    st.error("TTS produced empty audio.")
                    return

                # Persist audio
                with open(response_path, "rb") as f:
                    st.session_state.last_response_audio = f.read()
                
                # Log audio size for debugging
                audio_size = len(st.session_state.last_response_audio)
                logger.info(f"Generated audio size: {audio_size} bytes")

                os.unlink(response_path)

                # Rerender to show audio and update live transcription
                st.rerun()

            except Exception as e:
                logger.error(f"Voice error: {e}", exc_info=True)
                st.error(f"Error: {e}")

    st.caption("💡 Conversation continues in Live Transcription above")


# Validation functions
def validate_input(user_input: str) -> bool:
    """Basic validation"""
    if not user_input or not isinstance(user_input, str):
        return False
    
    cleaned = user_input.strip()
    if not cleaned or len(cleaned) > 1000:
        return False
    
    return True


def sanitize_input(user_input: str) -> str:
    """Sanitize input"""
    if not user_input:
        return ""
    
    sanitized = user_input.strip()
    sanitized = sanitized.replace('\x00', '')
    sanitized = ' '.join(sanitized.split())
    
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized


def validate_user_info_field(field_name: str, field_value: str) -> bool:
    """Validate user info"""
    # Keep your existing validation logic
    return True


if __name__ == "__main__":
    main()