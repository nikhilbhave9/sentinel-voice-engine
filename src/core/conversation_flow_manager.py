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


# def detect_escalation_from_tool_result(tool_result: Any) -> bool:
#     """
#     Detect if a tool result indicates escalation is needed.
    
#     Handles both dictionary and string tool responses for backward compatibility.
#     Checks for escalation_required field, status="not_supported", and action="escalate".
    
#     Args:
#         tool_result: The result returned from a tool call
    
#     Returns:
#         True if escalation is required, False otherwise
#     """
#     # Handle dictionary responses (new structured format)
#     if isinstance(tool_result, dict):
#         # Check explicit escalation_required field
#         if tool_result.get("escalation_required", False):
#             return True
#         # Check status field for "not_supported"
#         if tool_result.get("status") == "not_supported":
#             return True
#         # Check action field for "escalate"
#         if tool_result.get("action") == "escalate":
#             return True
    
#     # Handle string responses (legacy format for backward compatibility)
#     if isinstance(tool_result, str):
#         escalation_keywords = ["not_supported", "escalate", "specialist", "human agent"]
#         return any(keyword in tool_result.lower() for keyword in escalation_keywords)
    
#     return False


def process_message(message: str, state: ConversationStateData, source: str = "text") -> Dict[str, Any]:
    """
    Main message processing logic with automatic escalation detection
    
    Args:
        message: User's input message
        state: Current conversation state data
        source: Source of the message (voice/text), defaults to "text"
    
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
        llm_result = generate_response(full_prompt, context, state.conversation_history)
        
        # Extract response text and metadata
        response = llm_result.get("response", "")
        llm_latency_ms = llm_result.get("latency_ms", 0.0)
        token_count = llm_result.get("token_count", 0)
        model_name = llm_result.get("model_name", "")
        
        # 6. Check for escalation indicators in the response
        # Since automatic function calling is enabled, tool results are embedded in the response
        escalation_needed = _detect_escalation_in_response(response)
        
        if escalation_needed:
            # Check if we have the required information for escalation
            missing_info = []
            if not state.user_info.name:
                missing_info.append("name")
            if not state.user_info.contact_info:
                missing_info.append("phone number")
            
            if missing_info:
                # Request missing information before escalating
                missing_fields = " and ".join(missing_info)
                response = f"{response}\n\nBefore I connect you with a specialist, I'll need your {missing_fields}. Could you please provide that?"
            else:
                # We have all required info - trigger escalation
                escalation_msg = "I'll need a specialist for that. Let me get someone from the department on the line."
                
                # Import the tool here to avoid circular imports
                from src.core.tools import triage_and_escalate
                
                # Use the user's original message as the issue description
                issue_desc = message
                
                # Call the escalation tool
                triage_result = triage_and_escalate(
                    name=state.user_info.name,
                    issue_description=issue_desc,
                    phone=state.user_info.contact_info
                )
                
                # Append escalation message and result to response
                response = f"{response}\n\n{escalation_msg}\n\n{triage_result}"
            
        # Update conversation history
        state.add_message("user", message, source)
        state.add_message("assistant", response, source)
        
        return {
            "response": response,
            "new_state": new_state,
            "extracted_info": extracted_info,
            "intent": intent,
            "llm_latency_ms": llm_latency_ms,
            "token_count": token_count,
            "model_name": model_name
        }
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {
            "response": "I apologize, but I'm having trouble processing your message right now. Could you please try again?",
            "new_state": "error_handling",
            "extracted_info": {},
            "intent": "error",
            "llm_latency_ms": 0.0,
            "token_count": 0,
            "model_name": ""
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


def _detect_escalation_in_response(response: str) -> bool:
    """
    Detect if a response contains escalation indicators.
    
    This function checks the response text for keywords that indicate
    an escalation is needed, such as when a tool returns a "not_supported"
    status or mentions specialist assistance.
    
    Args:
        response: The response text from the LLM
    
    Returns:
        True if escalation indicators are found, False otherwise
    """
    if not response:
        return False
    
    response_lower = response.lower()
    
    # Check for escalation keywords that would appear in tool responses
    escalation_indicators = [
        "requires specialist assistance",
        "specialist assistance",
        "not_supported",
        "operation '",  # Part of the tool response message format
        "human agent",
        "escalate",
        "transfer to specialist",
        "connect you with a specialist"
    ]
    
    return any(indicator in response_lower for indicator in escalation_indicators)


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