"""
Simplified Streamlit Insurance Agent Application
Main application entry point with user interface and orchestration.
"""

import streamlit as st
import logging
import re
from typing import Dict, Any

from src.core.models import ConversationStateData, UserInfo
from src.core.conversation_flow_manager import process_message
from src.core.config import validate_required_config, get_api_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Application entry point"""
    try:
        st.set_page_config(
            page_title="Sentinel Insurance Agent",
            page_icon="🛡️",
            layout="wide"
        )
        
        st.title("🛡️ Sentinel Insurance Agent")
        st.markdown("*Your AI-powered insurance assistant*")
        
        # Initialize session state
        try:
            initialize_session_state()
        except Exception as e:
            logger.error(f"Session initialization error: {e}")
            st.error("Failed to initialize the application. Please refresh the page.")
            st.stop()
        
        # Check configuration
        try:
            if not validate_required_config():
                st.error("⚠️ Configuration Error: Please check your .env file and ensure GOOGLE_API_KEY is set.")
                st.info("Create a .env file in the project root with your Google API key:")
                st.code("GOOGLE_API_KEY=your_api_key_here")
                st.stop()
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            st.error("Unable to validate configuration. Please check your .env file.")
            st.stop()
        
        # Display conversation history
        try:
            display_conversation_history()
        except Exception as e:
            logger.error(f"Error displaying conversation history: {e}")
            st.error("Having trouble displaying conversation history.")
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        if user_input:
            handle_user_input(user_input)
            
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        st.error("The application encountered a critical error. Please refresh the page and try again.")
        st.info("If the problem persists, please check your configuration and try again later.")

def handle_user_input(user_input: str):
    """Process user messages"""
    try:
        # Validate and sanitize input
        if not validate_input(user_input):
            return  # Error message already shown by validate_input
        
        # Sanitize the input for safe processing
        sanitized_input = sanitize_input(user_input)
        if not sanitized_input:
            st.warning("Unable to process your message. Please try again.")
            return
        
        # Get current conversation state
        conversation_state = st.session_state.conversation_state
        
        # Add user message to display (use original input for display)
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Process message through conversation flow manager (use sanitized input)
        try:
            result = process_message(sanitized_input, conversation_state)
        except Exception as e:
            logger.error(f"Conversation flow error: {e}")
            st.error("I'm having trouble understanding your message. Could you please rephrase it?")
            # Add error response to conversation
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "I apologize, but I'm having trouble processing your request right now. Could you please try again or rephrase your message?"
            })
            st.rerun()
            return
        
        # Update conversation state
        conversation_state.current_state = result.get("new_state", conversation_state.current_state)
        
        # Add assistant response to display
        response = result.get("response", "I'm sorry, I couldn't process that request.")
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Log and validate extracted information
        extracted_info = result.get("extracted_info", {})
        if extracted_info:
            # Validate extracted information before storing
            validated_info = {}
            for field, value in extracted_info.items():
                if validate_user_info_field(field, value):
                    validated_info[field] = value
                else:
                    logger.warning(f"Invalid extracted {field}: {value}")
            
            if validated_info:
                logger.info(f"Validated extracted user info: {validated_info}")
        
        # Rerun to display new messages
        st.rerun()
        
    except Exception as e:
        logger.error(f"Unexpected error in handle_user_input: {e}")
        st.error("Sorry, I'm experiencing technical difficulties. Please try again in a moment.")
        # Add generic error response to conversation
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "I apologize for the technical issue. Please try your request again."
        })
        st.rerun()

def display_conversation_history():
    """Render chat history"""
    try:
        # Display all messages in the conversation
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Display current user info in sidebar if any is collected
        if hasattr(st.session_state, 'conversation_state'):
            user_info = st.session_state.conversation_state.user_info
            if any([user_info.name, user_info.policy_number, user_info.contact_info, user_info.inquiry_type]):
                try:
                    with st.sidebar:
                        st.subheader("📋 Collected Information")
                        if user_info.name:
                            st.text(f"Name: {user_info.name}")
                        if user_info.policy_number:
                            st.text(f"Policy: {user_info.policy_number}")
                        if user_info.contact_info:
                            st.text(f"Contact: {user_info.contact_info}")
                        if user_info.inquiry_type:
                            st.text(f"Type: {user_info.inquiry_type}")
                        
                        # Show current conversation state
                        st.text(f"State: {st.session_state.conversation_state.current_state}")
                except Exception as e:
                    logger.error(f"Error displaying sidebar info: {e}")
                    # Continue without sidebar - not critical
                    pass
                    
    except Exception as e:
        logger.error(f"Error displaying conversation history: {e}")
        st.error("Unable to display conversation history properly.")

def initialize_session_state():
    """Set up initial session state"""
    try:
        # Initialize messages list for chat display
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # Add welcome message
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Hello! I'm Sentinel, your AI insurance assistant. How can I help you today?"
            })
        
        # Initialize conversation state
        if "conversation_state" not in st.session_state:
            try:
                st.session_state.conversation_state = ConversationStateData()
            except Exception as e:
                logger.error(f"Error creating ConversationStateData: {e}")
                # Create a minimal fallback state
                st.session_state.conversation_state = type('ConversationState', (), {
                    'current_state': 'greeting',
                    'user_info': type('UserInfo', (), {
                        'name': None, 'policy_number': None, 
                        'contact_info': None, 'inquiry_type': None
                    })()
                })()
        
        # Initialize session metadata
        if "session_initialized" not in st.session_state:
            st.session_state.session_initialized = True
            logger.info("Session state initialized successfully")
            
    except Exception as e:
        logger.error(f"Critical error in initialize_session_state: {e}")
        raise  # Re-raise to be handled by main()

def validate_input(user_input: str) -> bool:
    """Basic input validation - replaces complex input_manager"""
    try:
        # Check if input exists and is a string
        if not user_input or not isinstance(user_input, str):
            return False
        
        # Check if input is not just whitespace
        cleaned_input = user_input.strip()
        if not cleaned_input:
            return False
        
        # Check reasonable length limits (prevent extremely long inputs)
        if len(cleaned_input) > 1000:
            st.warning("Message is too long. Please keep it under 1000 characters.")
            return False
        
        # Check for minimum length (prevent single character spam)
        if len(cleaned_input) < 1:
            return False
        
        # Basic content validation - check for suspicious patterns
        # Prevent potential injection attempts or malicious content
        suspicious_patterns = [
            r'<script[^>]*>',  # Script tags
            r'javascript:',    # JavaScript URLs
            r'data:text/html', # Data URLs
            r'vbscript:',      # VBScript
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, cleaned_input, re.IGNORECASE):
                st.warning("Invalid input detected. Please enter a normal message.")
                logger.warning(f"Suspicious input detected: {pattern}")
                return False
        
        # Check for excessive special characters (potential spam/gibberish)
        special_char_count = sum(1 for char in cleaned_input if not char.isalnum() and not char.isspace())
        if special_char_count > len(cleaned_input) * 0.5:  # More than 50% special characters
            st.warning("Please enter a more readable message with fewer special characters.")
            return False
        
        # Check for repeated characters (spam detection)
        if len(set(cleaned_input.lower())) < 3 and len(cleaned_input) > 10:
            st.warning("Please enter a more varied message.")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error in input validation: {e}")
        # If validation fails due to error, be conservative and reject
        st.warning("Unable to validate input. Please try again.")
        return False


def sanitize_input(user_input: str) -> str:
    """Sanitize user input for safe processing"""
    try:
        if not user_input:
            return ""
        
        # Basic sanitization
        sanitized = user_input.strip()
        
        # Remove any null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        # Limit length as additional safety
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
            logger.warning("Input truncated to 1000 characters")
        
        return sanitized
        
    except Exception as e:
        logger.error(f"Error sanitizing input: {e}")
        return ""


def validate_user_info_field(field_name: str, field_value: str) -> bool:
    """Validate specific user information fields"""
    try:
        if not field_value or not isinstance(field_value, str):
            return False
        
        field_value = field_value.strip()
        
        if field_name == "name":
            # Name should be 2-50 characters, letters and spaces only
            if not (2 <= len(field_value) <= 50):
                return False
            if not all(char.isalpha() or char.isspace() for char in field_value):
                return False
            return True
            
        elif field_name == "policy_number":
            # Policy number should be alphanumeric, 6-20 characters
            if not (6 <= len(field_value) <= 20):
                return False
            if not field_value.replace('-', '').replace('_', '').isalnum():
                return False
            return True
            
        elif field_name == "contact_info":
            # Basic email or phone validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            phone_pattern = r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
            
            if re.match(email_pattern, field_value) or re.match(phone_pattern, field_value):
                return True
            return False
            
        elif field_name == "inquiry_type":
            # Inquiry type should be one of the expected values
            valid_types = ["support", "sales", "general", "claim", "policy", "quote"]
            return field_value.lower() in valid_types
        
        return True  # Default to valid for unknown fields
        
    except Exception as e:
        logger.error(f"Error validating user info field {field_name}: {e}")
        return False

if __name__ == "__main__":
    main()