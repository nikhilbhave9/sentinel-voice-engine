"""
Simplified conversation logic and state management.
Handles intent detection, state transitions, and user information extraction.
Integrates directly with Streamlit session_state and simplified Gemini client.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from .models import ConversationState, UserInfo, ConversationStateData
from .prompts import (
    get_system_prompt, 
    get_intent_patterns, 
    get_info_extraction_patterns,
    INTENT_PATTERNS
)
from src.integration.gemini_client import generate_response

logger = logging.getLogger(__name__)


def process_message(message: str, state: ConversationStateData) -> Dict[str, Any]:
    """
    Main message processing logic
    
    Args:
        message: User's input message
        state: Current conversation state data
    
    Returns:
        Dictionary containing response, new_state, and extracted_info
    """
    try:
        # 1. Detect Intent
        intent = determine_intent(message)
        
        # 2. Extract info BEFORE generating response
        extracted_info = {}
        for field in ['name', 'policy_number', 'contact_info', 'inquiry_type']:
            val = extract_user_info(message, field)
            if val:
                setattr(state.user_info, field, val)
                extracted_info[field] = val

        # 3. Transition State
        new_state = transition_state(state.current_state, intent)
        state.current_state = new_state # Update the state object!

        # 4. Build context including the new state
        context = _build_context(state, extracted_info)

        # 5. Hybrid Context
        # Tell the LLM specifically what happened in this turn
        trigger_context = f"\n[SYSTEM NOTE: User intent detected as {intent}. Current State: {new_state}]"
        action_nudge = "\nInstruction: If you have enough info to call a tool, do it now."
        
        system_prompt = get_system_prompt(new_state)
        
        full_prompt = f"{system_prompt}{action_nudge}{trigger_context}\n\nUser: {message}"
        response = generate_response(full_prompt, context, state.conversation_history)
            
        # Update conversation history
        state.add_message("user", message)
        state.add_message("assistant", response)
        
        return {
            "response": response,
            "new_state": new_state,
            "extracted_info": extracted_info,
            "intent": intent
        }
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {
            "response": "I apologize, but I'm having trouble processing your message right now. Could you please try again?",
            "new_state": "error_handling",
            "extracted_info": {},
            "intent": "error"
        }


def extract_user_info(message: str, field_name: str) -> Optional[str]:
    """
    Extract user information from message
    
    Args:
        message: User's input message
        field_name: Type of information to extract (name, policy_number, contact_info, inquiry_type)
    
    Returns:
        Extracted information or None if not found
    """
    if not isinstance(message, str) or not isinstance(field_name, str) or not message.strip():
        return None
    
    patterns = get_info_extraction_patterns(field_name)
    
    for pattern in patterns:
        # Use original message for extraction, not lowercased version
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            
            # Special handling for different field types
            if field_name == 'name':
                # Capitalize names properly
                return ' '.join(word.capitalize() for word in extracted.split())
            elif field_name == 'inquiry_type':
                # Map to standard inquiry types (use lowercase for matching)
                extracted_lower = extracted.lower()
                if any(word in extracted_lower for word in ['support', 'help', 'assistance', 'problem', 'issue', 'claim']):
                    return 'support'
                elif any(word in extracted_lower for word in ['sales', 'buy', 'purchase', 'quote', 'insurance']):
                    return 'sales'
                return extracted_lower
            else:
                # For policy_number and contact_info, preserve original case
                if field_name == 'contact_info':
                    return extracted
                
                if field_name == 'policy_number':
                    return normalize_policy_number(extracted)

                return extracted
    
    return None


def determine_intent(message: str) -> str:
    """
    Classify user intent from message
    
    Args:
        message: User's input message
    
    Returns:
        Detected intent (greeting, support, sales, general)
    """
    if not isinstance(message, str) or not message.strip():
        return "general"
    
    message_lower = message.lower()
    
    # Check intents in priority order (most specific first)
    intent_priority = ["support", "sales", "greeting"]
    
    for intent in intent_priority:
        patterns = get_intent_patterns(intent)
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return intent
    
    return "general"


def transition_state(current_state: str, intent: str) -> str:
    """
    Manage conversation state transitions
    
    Args:
        current_state: Current conversation state
        intent: Detected user intent
    
    Returns:
        New conversation state
    """
    # State transition logic
    if intent == "support":
        return "support_flow"
    elif intent == "sales":
        return "sales_flow"
    elif intent == "greeting" and current_state == "error_handling":
        return "greeting"
    elif current_state == "error_handling":
        # Try to recover based on intent
        if intent in ["support", "sales"]:
            return f"{intent}_flow"
        return "greeting"
    
    # Stay in current state for general conversation
    return current_state if current_state in ["greeting", "support_flow", "sales_flow"] else "greeting"


def _build_context(state, extracted_info: dict = None) -> str:
    """
    Constructs the context string for the LLM.
    Combines the long-term state data with any information 
    just extracted in the current turn.
    """
    context_parts = ["### INTERNAL AGENT STATE ###"]
    
    # 1. Pull existing data from state.user_info
    # We use .get() or getattr() depending on how your state object is structured
    user_data = {
        "name": getattr(state.user_info, 'name', None),
        "phone": getattr(state.user_info, 'contact_info', None),
        "policy_id": getattr(state.user_info, 'policy_number', None)
    }
    
    # 2. Add turn-specific extracted info (to make sure it's fresh)
    if extracted_info:
        for key, value in extracted_info.items():
            if value:
                user_data[key] = value

    # 3. Format the data string
    known_data = ", ".join([f"{k}: {v}" for k, v in user_data.items() if v])
    if known_data:
        context_parts.append(f"AVAILABLE_DATA: {known_data}")
        
    # 4. Add the Current Phase (State Machine position)
    context_parts.append(f"CURRENT_PHASE: {state.current_state}")
    
    # 5. Add a "Missing Info" nudge if we are in a specific state
    if state.current_state == "SALES" and not user_data["phone"]:
        context_parts.append("MISSING_REQUIRED: Phone number needed for quote.")

    return "\n".join(context_parts)


def normalize_policy_number(raw_text: str) -> str:
    """
    Cleans transcription artifacts like 'P-O-L' or 'P O L' 
    into a standard format like 'POL'.
    """
    if not raw_text:
        return ""

    # Remove all non-alphanumeric characters (dashes, spaces, dots, etc.)
    # This turns "P-O-L - 1 2 3" -> "POL123"
    cleaned = re.sub(r'[^A-Za-z0-9]', '', raw_text)
    
    # Convert to uppercase to match DB keys
    return cleaned.upper()