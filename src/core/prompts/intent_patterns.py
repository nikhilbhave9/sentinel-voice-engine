"""
Intent detection patterns for the Sentinel Insurance Agent.

This module contains regex patterns used to detect user intents from their input,
helping to route conversations to appropriate flows (greeting, support, sales, general).
"""

from typing import Dict, List
from enum import Enum


class IntentType(Enum):
    """Types of user intents that can be detected."""
    GREETING = "greeting"
    SUPPORT = "support"
    SALES = "sales"
    GENERAL = "general"
    UNCLEAR = "unclear"


class IntentPatterns:
    """Container for all intent detection patterns."""
    
    @staticmethod
    def get_all_patterns() -> Dict[IntentType, List[str]]:
        """
        Returns all intent detection patterns.
        
        Returns:
            Dictionary mapping intent types to their regex patterns
        """
        return {
            IntentType.GREETING: IntentPatterns.GREETING_PATTERNS,
            IntentType.SUPPORT: IntentPatterns.SUPPORT_PATTERNS,
            IntentType.SALES: IntentPatterns.SALES_PATTERNS,
            IntentType.GENERAL: IntentPatterns.GENERAL_PATTERNS,
        }
    
    @staticmethod
    def get_patterns(intent_type: IntentType) -> List[str]:
        """
        Get patterns for a specific intent type.
        
        Args:
            intent_type: The intent type to get patterns for
            
        Returns:
            List of regex patterns for the intent type
        """
        all_patterns = IntentPatterns.get_all_patterns()
        return all_patterns.get(intent_type, [])
    
    # Greeting Intent Patterns
    GREETING_PATTERNS = [
        r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b",
        r"\b(start|begin|new conversation)\b",
        r"^(hi|hello|hey)[\s!.]*$",
    ]
    
    # Support Intent Patterns
    SUPPORT_PATTERNS = [
        r"\b(help|support|assistance|problem|issue|trouble)\b",
        r"\b(claim|policy|coverage|benefits)\b",
        r"\b(can't|cannot|unable|difficulty|error)\b",
        r"\b(fix|resolve|solve|repair)\b",
        r"\b(existing|current|my policy)\b",
    ]
    
    # Sales Intent Patterns
    SALES_PATTERNS = [
        r"\b(buy|purchase|get|want|need|interested)\b.*\b(insurance|policy|coverage)\b",
        r"\b(quote|price|cost|rate|premium)\b",
        r"\b(new|additional|more) (insurance|policy|coverage)\b",
        r"\b(auto|car|home|life|health) insurance\b",
        r"\b(sign up|enroll|apply)\b",
    ]
    
    # General Intent Patterns
    GENERAL_PATTERNS = [
        r"\b(information|info|about|what|how|when|where|why)\b",
        r"\b(explain|tell me|describe)\b",
        r"\b(question|ask|wondering)\b",
    ]