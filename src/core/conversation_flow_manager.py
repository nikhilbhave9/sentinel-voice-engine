import re
from typing import Dict, Optional, List, Tuple
from .models import ConversationState, UserInfo
from .prompts import SystemPrompts, IntentPatterns, InfoCollectionPatterns
from .prompts.intent_patterns import IntentType


class ConversationFlowManager:
    """
    Manages conversation state transitions and context awareness.
    
    This class handles:
    - State transition logic for greeting, support_flow, sales_flow
    - Intent detection for routing user inputs to appropriate flows
    - System prompts for different conversation states
    - Information collection guidance
    """
    
    def __init__(self):
        self.intent_patterns = IntentPatterns.get_all_patterns()
        self.system_prompts = SystemPrompts.get_all_prompts()
        self.info_collection_triggers = InfoCollectionPatterns.get_collection_triggers()
    
    def determine_next_state(
        self, 
        current_state: str, 
        user_input: str, 
        user_info: Optional[UserInfo] = None
    ) -> str:
        """
        Analyzes user input to determine the next conversation state.
        
        Args:
            current_state: Current conversation state
            user_input: User's message content
            user_info: Current user information (optional)
            
        Returns:
            Next conversation state as string
        """
        if not isinstance(current_state, str):
            raise ValueError("current_state must be a string")
        
        if not isinstance(user_input, str):
            raise ValueError("user_input must be a string")
        
        if not user_input.strip():
            return current_state  # No change for empty input
        
        # Validate current state
        valid_states = [state.value for state in ConversationState]
        if current_state not in valid_states:
            current_state = ConversationState.GREETING.value
        
        # Detect user intent
        intent = self._detect_intent(user_input)
        
        # Apply state transition logic
        return self._apply_state_transition_logic(current_state, intent, user_info)
    
    def get_system_prompt(self, state: str) -> str:
        """
        Returns appropriate system prompt for the given conversation state.
        
        Args:
            state: Current conversation state
            
        Returns:
            System prompt string for the state
        """
        if not isinstance(state, str):
            raise ValueError("state must be a string")
        
        valid_states = [state_enum.value for state_enum in ConversationState]
        if state not in valid_states:
            state = ConversationState.GREETING.value
        
        return SystemPrompts.get_prompt(state)
    
    def should_collect_info(
        self, 
        state: str, 
        user_input: str, 
        user_info: Optional[UserInfo] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Determines if user information should be extracted from the input.
        
        Args:
            state: Current conversation state
            user_input: User's message content
            user_info: Current user information
            
        Returns:
            Tuple of (should_collect, field_name) where field_name is the field to collect
        """
        if not isinstance(state, str) or not isinstance(user_input, str):
            return False, None
        
        if not user_input.strip():
            return False, None
        
        if user_info is None:
            user_info = UserInfo()
        
        # Check if we should collect information based on state and triggers
        for field_name, patterns in self.info_collection_triggers.items():
            if user_info.has_field(field_name):
                continue  # Already collected this field
            
            for pattern in patterns:
                if re.search(pattern, user_input.lower()):
                    return True, field_name
        
        return False, None
    
    def extract_user_info(self, user_input: str, field_name: str) -> Optional[str]:
        """
        Extracts specific user information from input text.
        
        Args:
            user_input: User's message content
            field_name: Name of the field to extract
            
        Returns:
            Extracted information or None if not found
        """
        if not isinstance(user_input, str) or not isinstance(field_name, str):
            return None
        
        user_input = user_input.strip()
        if not user_input:
            return None
        
        # Define extraction patterns for different fields
        extraction_patterns = InfoCollectionPatterns.get_extraction_patterns()
        
        patterns = extraction_patterns.get(field_name, [])
        
        for pattern in patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                extracted = match.group(1).strip()
                if extracted:
                    # Clean up the extracted value
                    if field_name == 'name':
                        extracted = ' '.join(word.capitalize() for word in extracted.split())
                    elif field_name == 'policy_number':
                        # For policy numbers, preserve original case from the original input
                        original_match = re.search(pattern, user_input, re.IGNORECASE)
                        if original_match:
                            extracted = original_match.group(1).strip()
                    elif field_name == 'inquiry_type':
                        if any(word in extracted for word in ['support', 'help', 'assistance', 'problem', 'issue', 'claim']):
                            extracted = 'support'
                        elif any(word in extracted for word in ['sales', 'buy', 'purchase', 'quote', 'new', 'insurance']):
                            extracted = 'sales'
                        else:
                            extracted = 'general'
                    
                    return extracted
        
        return None
    
    def _detect_intent(self, user_input: str) -> IntentType:
        """
        Detects user intent from input text.
        
        Args:
            user_input: User's message content
            
        Returns:
            Detected intent type
        """
        user_input_lower = user_input.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    return intent
        
        return IntentType.GENERAL
    
    def _apply_state_transition_logic(
        self, 
        current_state: str, 
        intent: IntentType, 
        user_info: Optional[UserInfo] = None
    ) -> str:
        """
        Applies state transition logic based on current state and detected intent.
        
        Args:
            current_state: Current conversation state
            intent: Detected user intent
            user_info: Current user information
            
        Returns:
            Next conversation state
        """
        # State transition rules
        if current_state == ConversationState.GREETING.value:
            if intent == IntentType.SUPPORT:
                return ConversationState.SUPPORT_FLOW.value
            elif intent == IntentType.SALES:
                return ConversationState.SALES_FLOW.value
            else:
                return ConversationState.GREETING.value
        
        elif current_state == ConversationState.SUPPORT_FLOW.value:
            if intent == IntentType.SALES:
                return ConversationState.SALES_FLOW.value
            elif intent == IntentType.GREETING:
                return ConversationState.GREETING.value
            else:
                return ConversationState.SUPPORT_FLOW.value
        
        elif current_state == ConversationState.SALES_FLOW.value:
            if intent == IntentType.SUPPORT:
                return ConversationState.SUPPORT_FLOW.value
            elif intent == IntentType.GREETING:
                return ConversationState.GREETING.value
            else:
                return ConversationState.SALES_FLOW.value
        
        elif current_state == ConversationState.ERROR_HANDLING.value:
            # Always try to recover to appropriate state based on intent
            if intent == IntentType.SUPPORT:
                return ConversationState.SUPPORT_FLOW.value
            elif intent == IntentType.SALES:
                return ConversationState.SALES_FLOW.value
            else:
                return ConversationState.GREETING.value
        
        # Default fallback
        return current_state
    
    def get_available_states(self) -> List[str]:
        """Returns list of all available conversation states."""
        return [state.value for state in ConversationState]
    
    def is_valid_state(self, state: str) -> bool:
        """Checks if the given state is valid."""
        return state in self.get_available_states()
    
    def get_state_description(self, state: str) -> str:
        """Returns a human-readable description of the conversation state."""
        descriptions = {
            ConversationState.GREETING.value: "Initial greeting and needs assessment",
            ConversationState.SUPPORT_FLOW.value: "Helping with existing policy support",
            ConversationState.SALES_FLOW.value: "Assisting with new insurance purchases",
            ConversationState.ERROR_HANDLING.value: "Recovering from system errors"
        }
        return descriptions.get(state, "Unknown state")