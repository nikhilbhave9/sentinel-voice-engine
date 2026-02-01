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
        # Determine intent and next state
        intent = determine_intent(message)
        new_state = transition_state(state.current_state, intent)
        
        # Extract user information if present
        extracted_info = {}
        for field in ['name', 'policy_number', 'contact_info', 'inquiry_type']:
            if not getattr(state.user_info, field):  # Only extract if not already collected
                extracted_value = extract_user_info(message, field)
                if extracted_value:
                    extracted_info[field] = extracted_value
                    setattr(state.user_info, field, extracted_value)
        
        # Get system prompt for current state
        system_prompt = get_system_prompt(new_state)
        
        # Build context from conversation history
        context = _build_context(state, extracted_info)
        
        # Generate response using Gemini
        full_prompt = f"{system_prompt}\n\nUser: {message}"
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


def _build_context(state: ConversationStateData, extracted_info: Dict[str, str]) -> str:
    """
    Build context string from conversation state and extracted info
    
    Args:
        state: Current conversation state data
        extracted_info: Recently extracted user information
    
    Returns:
        Context string for the AI
    """
    context_parts = []
    
    # Add user information context
    if state.user_info.name:
        context_parts.append(f"Customer name: {state.user_info.name}")
    if state.user_info.policy_number:
        context_parts.append(f"Policy number: {state.user_info.policy_number}")
    if state.user_info.contact_info:
        context_parts.append(f"Contact info: {state.user_info.contact_info}")
    if state.user_info.inquiry_type:
        context_parts.append(f"Inquiry type: {state.user_info.inquiry_type}")
    
    # Add recently extracted information
    if extracted_info:
        context_parts.append("Recently provided information:")
        for field, value in extracted_info.items():
            context_parts.append(f"- {field}: {value}")
    
    # Add conversation history context (last few messages)
    if state.conversation_history:
        recent_messages = state.conversation_history[-4:]  # Last 2 exchanges
        if recent_messages:
            context_parts.append("Recent conversation:")
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:100]  # Truncate long messages
                context_parts.append(f"{role}: {content}")
    
    return "\n".join(context_parts) if context_parts else ""