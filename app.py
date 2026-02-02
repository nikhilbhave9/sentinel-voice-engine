import streamlit as st
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


def main():
    """Application entry point"""
    config_settings = get_settings()
    
    st.set_page_config(
        page_title=config_settings.app_title,
        page_icon="🛡️",
        layout="wide"
    )
    
    st.title("🛡️ Sentinel Insurance Agent")
    st.markdown("*Your AI-powered insurance assistant*")
    
    initialize_session_state()
    
    # Tabs for text vs voice
    tab1, tab2 = st.tabs(["💬 Text Chat", "🎙️ Voice Call"])
    
    with tab1:
        render_text_chat_interface()
    
    with tab2:
        render_voice_call_interface()


def initialize_session_state():
    """Initialize session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I'm Sentinel. How can I help you today?",
            "source": "text"
        })
    
    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = ConversationStateData()
    
    if "voice_handler" not in st.session_state:
        st.session_state.voice_handler = None
        st.session_state.models_loaded = False
    
    # CRITICAL: Track processed audio to prevent re-processing
    if "last_processed_audio_hash" not in st.session_state:
        st.session_state.last_processed_audio_hash = None
    
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
        result = process_message(sanitized, st.session_state.conversation_state)
        
        # Update state
        st.session_state.conversation_state.current_state = result.get(
            "new_state", 
            st.session_state.conversation_state.current_state
        )
        
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


def display_conversation_history():
    """Display conversation with source indicators"""
    for msg in st.session_state.messages:
        source = msg.get("source", "text")
        icon = "🎤" if source == "voice" else "💬"
        
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.caption(f"{icon} {source.capitalize()}")
            st.markdown(msg["content"])


def render_text_chat_interface():
    """Text chat interface"""
    display_conversation_history()
    
    user_input = st.chat_input("Type your message...")
    if user_input:
        handle_user_input(user_input, is_voice=False)
        st.rerun()


def render_voice_call_interface():
    """Voice interface with persistent audio + loop prevention"""
    st.markdown("### Conversation History")
    display_conversation_history()
    
    st.markdown("---")
    st.markdown("### 🎤 Voice Input")

    # ---- INIT AUDIO STATE ----
    if "last_response_audio" not in st.session_state:
        st.session_state.last_response_audio = None

    # ---- LOAD MODELS ----
    if not st.session_state.models_loaded:
        if st.button("🚀 Load Voice Models (one-time)", type="primary"):
            with st.spinner("Loading models (~15 seconds)..."):
                try:
                    st.session_state.voice_handler = StreamlitVoiceHandler(
                        st.session_state.conversation_state
                    )
                    _ = st.session_state.voice_handler.stt_model
                    _ = st.session_state.voice_handler.tts_model
                    st.session_state.models_loaded = True
                    st.success("✅ Models loaded!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"Model loading error: {e}", exc_info=True)
                    st.error(f"Failed to load: {e}")
        st.info("👆 Click to initialize voice (required once)")
        return

    # ---- PLAY LAST AGENT AUDIO (PERSISTENT + AUTOPLAY) ----
    if st.session_state.last_response_audio:
        st.markdown("### 🔊 Agent Response")
        # Added autoplay=True so the user actually hears it immediately
        st.audio(
            st.session_state.last_response_audio, 
            format="audio/wav", 
            autoplay=True 
        )

    # ---- AUDIO RECORDER ----
    st.caption("Click microphone to record")

    audio_bytes = audio_recorder(
        text="",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_name="microphone",
        icon_size="2x",
        key="voice_recorder"
    )

    # ---- PROCESS NEW AUDIO ----
    if audio_bytes:
        audio_hash = hashlib.md5(audio_bytes).hexdigest()

        if audio_hash == st.session_state.last_processed_audio_hash:
            logger.info("Skipping already processed audio")
            return

        st.session_state.last_processed_audio_hash = audio_hash

        with st.expander("🎧 Your Recording", expanded=False):
            st.audio(audio_bytes, format="audio/wav")

        with st.spinner("🎯 Processing..."):
            try:
                # Save mic audio
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    audio_path = tmp.name

                handler = st.session_state.voice_handler

                # STT
                transcription = handler.transcribe_audio(audio_path)
                os.unlink(audio_path)

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

                # TTS
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    response_path = tmp.name

                handler.synthesize_speech(last_response, response_path)

                # Validate audio
                if os.path.getsize(response_path) == 0:
                    os.unlink(response_path)
                    st.error("TTS produced empty audio.")
                    return

                # Persist audio
                with open(response_path, "rb") as f:
                    st.session_state.last_response_audio = f.read()

                os.unlink(response_path)

                # Rerender to show audio
                st.rerun()

            except Exception as e:
                logger.error(f"Voice error: {e}", exc_info=True)
                st.error(f"Error: {e}")

    st.caption("💡 Conversation continues above. Ask follow-ups!")


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