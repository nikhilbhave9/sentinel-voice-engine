"""
Simplified conversation logic and state management.
Handles intent detection, state transitions, and user information extraction.
Integrates directly with Streamlit session_state and simplified Gemini client.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from .models import ConversationState, UserInfo, ConversationStateData
from src.integration.gemini_client import generate_response

logger = logging.getLogger(__name__)

# Intent patterns for classification
INTENT_PATTERNS = {
    "greeting": [
        r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b",
        r"\b(start|begin|new conversation)\b",
        r"^(hi|hello|hey)[\s!.]*$",
    ],
    "support": [
        r"\b(help|support|assistance|problem|issue|trouble)\b",
        r"\b(claim|policy|coverage|benefits)\b",
        r"\b(can't|cannot|unable|difficulty|error)\b",
        r"\b(fix|resolve|solve|repair)\b",
        r"\b(existing|current|my policy)\b",
    ],
    "sales": [
        r"\b(buy|purchase|get|want|need|interested)\b.*\b(insurance|policy|coverage)\b",
        r"\b(quote|price|cost|rate|premium)\b",
        r"\b(new|additional|more) (insurance|policy|coverage)\b",
        r"\b(auto|car|home|life|health) insurance\b",
        r"\b(sign up|enroll|apply)\b",
    ]
}

# System prompts for different states
SYSTEM_PROMPTS = {
    "greeting": """You are Sentinel, a helpful AI insurance agent. You are greeting a new customer or continuing a conversation. 

Your role is to:
- Welcome customers warmly and professionally
- Understand what they need help with (support for existing policies or sales for new insurance)
- Guide them to the appropriate conversation flow
- Collect basic information like their name if they haven't provided it

Keep responses friendly, concise, and focused on understanding their needs. Ask clarifying questions to determine if they need support with existing policies or are interested in new insurance products.""",
    
    "support_flow": """You are Sentinel, a helpful AI insurance agent in support mode. The customer needs help with their existing insurance policy or has questions about their coverage.

Your role is to:
- Help with policy questions, claims, coverage details, and account issues
- Collect relevant information like policy numbers when needed
- Provide clear explanations about their benefits and coverage
- Guide them through processes like filing claims or updating their information
- Escalate complex issues to human agents when appropriate

Be empathetic, thorough, and solution-focused. Always prioritize the customer's immediate needs and concerns.""",
    
    "sales_flow": """You are Sentinel, a helpful AI insurance agent in sales mode. The customer is interested in purchasing new insurance or learning about insurance products.

Your role is to:
- Understand their insurance needs and current situation
- Explain different types of insurance products available
- Provide general information about coverage options and benefits
- Collect basic information to help determine their needs
- Guide them toward getting quotes or speaking with a sales specialist

Be informative, helpful, and consultative. Focus on understanding their needs rather than being pushy. Provide educational information to help them make informed decisions.""",
    
    "error_handling": """You are Sentinel, a helpful AI insurance agent in error recovery mode. Something went wrong, but you're here to help get the conversation back on track.

Your role is to:
- Acknowledge any issues that occurred
- Reassure the customer that you're here to help
- Determine what they were trying to accomplish
- Guide them back to the appropriate conversation flow
- Provide alternative ways to get help if needed

Be apologetic for any inconvenience, patient, and focused on resolving their needs despite the technical issue."""
}

# Information extraction patterns
INFO_EXTRACTION_PATTERNS = {
    'name': [
        r"(?:my name is|i'm|i am|call me)\s+([a-zA-Z\s]{2,30}?)(?:\s+and|\s*,|\s*$)",
        r"^([a-zA-Z\s]{2,30}?)(?:\s+here|$)",  # Simple name at start
    ],
    'policy_number': [
        r"(?:policy number|policy|number)\s*(?:is|:)?\s*([a-zA-Z0-9\-]+)",
        r"\b([a-zA-Z]{2,3}\d{6,10})\b",  # Common policy format
        r"\b(\d{8,12})\b",  # Numeric policy
    ],
    'contact_info': [
        r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",  # Email
        r"(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})",  # Phone
    ],
    'inquiry_type': [
        r"\b(support|help|assistance|problem|issue|claim)\b",
        r"\b(sales|buy|purchase|quote|new policy|insurance)\b",
    ]
}


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
        system_prompt = SYSTEM_PROMPTS.get(new_state, SYSTEM_PROMPTS["greeting"])
        
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
    
    patterns = INFO_EXTRACTION_PATTERNS.get(field_name, [])
    
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
        patterns = INTENT_PATTERNS.get(intent, [])
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