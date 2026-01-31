"""
Consolidated prompt management for Sentinel Insurance Agent.

This module contains all system prompts, intent patterns, and response templates
consolidated from the original multi-file structure into a single, maintainable file.
"""

from typing import Dict, List


# System prompts for different conversation states
SYSTEM_PROMPTS: Dict[str, str] = {
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


# Intent detection patterns
INTENT_PATTERNS: Dict[str, List[str]] = {
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
    ],
    
    "general": [
        r"\b(information|info|about|what|how|when|where|why)\b",
        r"\b(explain|tell me|describe)\b",
        r"\b(question|ask|wondering)\b",
    ]
}


# Information collection patterns
INFO_COLLECTION_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "triggers": {
        "name": [
            r"\b(my name is|i'm|i am|call me)\b",
            r"\b(name|called)\b",
        ],
        
        "policy_number": [
            r"\b(policy|policy number|account number)\b",
            r"\b[a-zA-Z]{2,3}\d{6,10}\b",  # Policy-like format
            r"\b\d{8,12}\b",  # Long numeric string
        ],
        
        "contact_info": [
            r"@",  # Email indicator
            r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone pattern
            r"\b(email|phone|contact)\b",
        ],
        
        "inquiry_type": [
            r"\b(help|support|problem|issue|claim)\b",
            r"\b(buy|purchase|quote|new policy)\b",
        ]
    },
    
    "extraction": {
        "name": [
            r"(?:my name is|i'm|i am|call me)\s+([a-zA-Z\s]{2,30}?)(?:\s+and|\s*,|\s*$)",
            r"^([a-zA-Z\s]{2,30}?)(?:\s+here|$)",  # Simple name at start
        ],
        
        "policy_number": [
            r"(?:policy number|policy|number)\s*(?:is|:)?\s*([a-zA-Z0-9\-]+)",
            r"\b([a-zA-Z]{2,3}\d{6,10})\b",  # Common policy format
            r"\b(\d{8,12})\b",  # Numeric policy
        ],
        
        "contact_info": [
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",  # Email
            r"(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})",  # Phone
        ],
        
        "inquiry_type": [
            r"\b(support|help|assistance|problem|issue|claim)\b",
            r"\b(sales|buy|purchase|quote|new policy|insurance)\b",
        ]
    }
}


# Response templates for common scenarios
RESPONSE_TEMPLATES: Dict[str, str] = {
    "greeting": "Hello! I'm Sentinel, your AI insurance assistant. How can I help you today?",
    
    "support_greeting": "I'd be happy to help you with your support request. Could you tell me more about what you need assistance with?",
    
    "sales_greeting": "I can help you find the right insurance coverage for your needs. What type of insurance are you interested in?",
    
    "name_request": "To better assist you, could you please tell me your name?",
    
    "policy_request": "Could you please provide your policy number so I can look up your account?",
    
    "contact_request": "Could you please provide your email address or phone number for our records?",
    
    "clarification_request": "I want to make sure I understand correctly. Could you please provide a bit more detail about what you're looking for?",
    
    "error_recovery": "I apologize for any confusion. Let me help you get back on track. What can I assist you with today?",
    
    "escalation": "I understand this is important to you. Let me connect you with a specialist who can provide more detailed assistance.",
    
    "thank_you": "Thank you for providing that information. Let me help you with your request."
}


# Utility functions for accessing prompts
def get_system_prompt(state: str) -> str:
    """
    Get system prompt for a specific conversation state.
    
    Args:
        state: Conversation state string
        
    Returns:
        System prompt for the state, or greeting prompt if state not found
    """
    return SYSTEM_PROMPTS.get(state, SYSTEM_PROMPTS["greeting"])


def get_intent_patterns(intent_type: str) -> List[str]:
    """
    Get patterns for a specific intent type.
    
    Args:
        intent_type: The intent type to get patterns for
        
    Returns:
        List of regex patterns for the intent type
    """
    return INTENT_PATTERNS.get(intent_type, [])


def get_info_triggers(field_name: str) -> List[str]:
    """
    Get trigger patterns for a specific information field.
    
    Args:
        field_name: Name of the field to get triggers for
        
    Returns:
        List of trigger patterns for the field
    """
    return INFO_COLLECTION_PATTERNS["triggers"].get(field_name, [])


def get_info_extraction_patterns(field_name: str) -> List[str]:
    """
    Get extraction patterns for a specific information field.
    
    Args:
        field_name: Name of the field to get extraction patterns for
        
    Returns:
        List of extraction patterns for the field
    """
    return INFO_COLLECTION_PATTERNS["extraction"].get(field_name, [])


def get_response_template(template_name: str) -> str:
    """
    Get a response template by name.
    
    Args:
        template_name: Name of the template to retrieve
        
    Returns:
        Response template string, or empty string if not found
    """
    return RESPONSE_TEMPLATES.get(template_name, "")